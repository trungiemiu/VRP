import random

class Hospital:
    def __init__(self, hospital_id, demand_weight, demand_volume, earliest_time, latest_time,
                 beta=1.0, mu=1):
        self.hospital_id = hospital_id
        self.demand_weight = demand_weight
        self.demand_volume = demand_volume
        self.earliest_time = earliest_time
        self.latest_time = latest_time
        self.assigned = False
        self.beta = beta
        self.mu = mu

    @property
    def alpha(self):
        return 0.4 * self.beta + 0.6 * self.mu


class Vehicle:
    def __init__(self, vehicle_id, weight_capacity, volume_capacity, distance_capacity,
                 speed, fixed_cost, time_cost_coeff, distance_cost_coeff):
        self.vehicle_id = vehicle_id
        self.weight_capacity = weight_capacity
        self.volume_capacity = volume_capacity
        self.distance_capacity = distance_capacity
        self.speed = speed
        self.fixed_cost = fixed_cost
        self.time_cost_coeff = time_cost_coeff
        self.distance_cost_coeff = distance_cost_coeff
        self.route = []  

    def add_hospital(self, h): self.route.append(h)
    def insert_hospital(self, i, h): self.route.insert(i, h)
    def remove_hospital(self, h): self.route.remove(h)

    def total_weight(self): return sum(h.demand_weight for h in self.route)
    def total_volume(self): return sum(h.demand_volume for h in self.route)

    def total_distance(self, D):
        if not self.route: return 0.0
        last, s = 0, 0.0
        for h in self.route:
            s += D[last][h.hospital_id]; last = h.hospital_id
        s += D[last][0]
        return s

    def travel_time(self, D):
        d = self.total_distance(D)
        return 0.0 if d == 0 else d / self.speed

    def arrival_times(self, D, start=8.0):
        t, last = start, 0
        at = {}
        for h in self.route:
            t += D[last][h.hospital_id] / self.speed
            at[h.hospital_id] = t
            last = h.hospital_id
        return at

    def penalty(self, D, penalties, time_scale=6.0):
        cost, at = 0.0, self.arrival_times(D)
        for h in self.route:
            a = at[h.hospital_id]
            if a < h.earliest_time:
                cost += h.alpha * penalties["early"] * (h.earliest_time - a) * time_scale
            elif a > h.latest_time:
                cost += h.alpha * penalties["late"]  * (a - h.latest_time) * time_scale
        return cost

    def load_distance_cost(self, D, coeff):
        if not self.route: return 0.0
        cost, last = 0.0, 0
        remaining = sum(h.demand_volume for h in self.route)
        for h in self.route:
            d = D[last][h.hospital_id]
            cost += coeff * d * remaining
            remaining -= h.demand_volume
            last = h.hospital_id
        return cost

    def vehicle_cost(self, D, penalties, use_load_distance_cost=True, time_scale=6.0):
        if not self.route: return 0.0
        time_c = self.travel_time(D) * self.time_cost_coeff
        dist_c = (self.load_distance_cost(D, self.distance_cost_coeff)
                  if use_load_distance_cost else
                  self.total_distance(D) * self.distance_cost_coeff)
        pen_c  = self.penalty(D, penalties, time_scale)
        return self.fixed_cost + time_c + dist_c + pen_c

    def feasible(self, D):
        return (self.total_weight()   <= self.weight_capacity and
                self.total_volume()   <= self.volume_capacity and
                self.total_distance(D) <= self.distance_capacity)

    def print_info(self, D, penalties, use_load_distance_cost=True, time_scale=6.0):
        ids = [h.hospital_id for h in self.route]
        print(f"Vehicle {self.vehicle_id}:")
        print(f"  Route: {ids}")
        for hid, t in self.arrival_times(D).items():
            print(f"    Hospital {hid}: {t:.2f}")
        print(f"  Total Distance: {self.total_distance(D):.2f}")
        print(f"  Total Travel Time: {self.travel_time(D):.2f}")
        print(f"  Vehicle Cost: {self.vehicle_cost(D, penalties, use_load_distance_cost, time_scale):.2f}")


class Solution:
    def __init__(self, vehicles, hospitals, distances):
        self.vehicles = vehicles
        self.hospitals = hospitals
        self.distances = distances

    def deepcopy(self):
        vs = []
        for v in self.vehicles:
            nv = Vehicle(v.vehicle_id, v.weight_capacity, v.volume_capacity, v.distance_capacity,
                         v.speed, v.fixed_cost, v.time_cost_coeff, v.distance_cost_coeff)
            nv.route = list(v.route)
            vs.append(nv)
        return Solution(vs, self.hospitals, self.distances)

    def assign_initial(self):
        random.shuffle(self.hospitals)
        for h in self.hospitals:
            if h.assigned:
                continue
            random.shuffle(self.vehicles)
            placed = False
            for v in self.vehicles:
                v.add_hospital(h)
                if v.feasible(self.distances):
                    h.assigned = True; placed = True; break
                v.remove_hospital(h)
            if not placed:
                for v in self.vehicles:
                    v.insert_hospital(0, h)
                    if v.feasible(self.distances):
                        h.assigned = True; placed = True; break
                    v.remove_hospital(h)
            if not placed:
                raise ValueError(f"Cannot assign hospital {h.hospital_id}")

    def total_cost(self, penalties, use_load_distance_cost=True, time_scale=6.0):
        return sum(v.vehicle_cost(self.distances, penalties, use_load_distance_cost, time_scale)
                   for v in self.vehicles)

    def print_info(self, penalties, use_load_distance_cost=True, time_scale=6.0):
        for v in self.vehicles:
            v.print_info(self.distances, penalties, use_load_distance_cost, time_scale)

