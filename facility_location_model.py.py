import pandas as pd
import pulp
import folium
import os
from geopy.distance import geodesic

project_path = r'E:\UOP\Project\Facility Location'

os.chdir(project_path)

print("Current Working Directory:")
print(os.getcwd())


# DEFINE WAREHOUSES AND STORES
warehouses = ['W1', 'W2', 'W3', 'W4']
stores = ['S1', 'S2', 'S3', 'S4', 'S5','S6', 'S7', 'S8', 'S9', 'S10']


# FIXED COST OF WAREHOUSES
fixed_cost = {
    'W1': 5000,   # Colombo
    'W2': 3500,   # Kandy
    'W3': 4000,   # Kurunegala
    'W4': 3000    # Galle
}


# WAREHOUSE CAPACITY
capacity = {
    'W1': 400,
    'W2': 300,
    'W3': 450,
    'W4': 350
}


# STORE DEMAND
demand = {
    'S1': 80,
    'S2': 75,
    'S3': 120,
    'S4': 70,
    'S5': 95,
    'S6': 110,
    'S7': 60,
    'S8': 85,
    'S9': 90,
    'S10': 65
}


# LOCATION DATA
locations = {

    # Warehouses
    'W1': (6.9271, 79.8612),   # Colombo
    'W2': (7.2906, 80.6337),   # Kandy
    'W3': (7.4863, 80.3623),   # Kurunegala
    'W4': (6.0535, 80.2210),   # Galle

    # Stores
    'S1': (7.2083, 79.8358),   # Negombo
    'S2': (7.0873, 79.9994),   # Gampaha
    'S3': (6.7132, 79.9026),   # Moratuwa
    'S4': (6.5854, 79.9607),   # Kalutara
    'S5': (7.8731, 80.6511),   # Dambulla
    'S6': (8.3114, 80.4037),   # Anuradhapura
    'S7': (6.9497, 80.7891),   # Nuwara Eliya
    'S8': (6.0329, 80.2168),   # Matara
    'S9': (6.1429, 81.1212),   # Hambantota
    'S10': (7.3402, 80.6337)   # Matale
}


# CALCULATE TRANSPORTATION COST USING DISTANCE
transport_cost = {}

for w in warehouses:
    for s in stores:
        # Calculate distance in KM
        distance = geodesic(locations[w], locations[s]).km
        # Cost per KM
        cost = distance * 2
        # Store transportation cost
        transport_cost[(w, s)] = round(cost, 2)


# CREATE OPTIMIZATION MODEL
model = pulp.LpProblem(
    "Facility_Location_Problem",
    pulp.LpMinimize
)


# DECISION VARIABLES
# Warehouse opening variable
y = pulp.LpVariable.dicts("OpenWarehouse",warehouses,lowBound=0,upBound=1,cat='Binary')
# Store assignment variable
x = pulp.LpVariable.dicts("Assign",[(w, s) for w in warehouses for s in stores],lowBound=0,upBound=1,cat='Binary')

# OBJECTIVE FUNCTION
model += (pulp.lpSum(fixed_cost[w] * y[w]for w in warehouses)
          +pulp.lpSum(transport_cost[(w, s)] * x[(w, s)]for w in warehouses for s in stores)
          )


# CONSTRAINT 1
# EACH STORE MUST BE SERVED BY ONE WAREHOUSE
for s in stores:
    model += pulp.lpSum(x[(w, s)] for w in warehouses) == 1

# CONSTRAINT 2
# STORE CAN ONLY BE ASSIGNED TO OPEN WAREHOUSE
for w in warehouses:
    for s in stores:
        model += x[(w, s)] <= y[w]


# CONSTRAINT 3
# WAREHOUSE CAPACITY
for w in warehouses:
    model += pulp.lpSum(demand[s] * x[(w, s)]for s in stores) <= capacity[w] * y[w]


# SOLVE MODEL
model.solve()
print("\n==============================")
print("MODEL STATUS")
print(pulp.LpStatus[model.status])


# OPENED WAREHOUSES
print("\n==============================")
print("OPENED WAREHOUSES")
opened_warehouses = []
for w in warehouses:
    if y[w].value() == 1:
        print(w)
        opened_warehouses.append(w)

# STORE ASSIGNMENTS
print("\n==============================")
print("STORE ASSIGNMENTS")
assignments = []

for w in warehouses:
    for s in stores:
        if x[(w, s)].value() == 1:
            cost = transport_cost[(w, s)]
            print(f"{s} served by {w} | Transport Cost = {cost}")
            assignments.append([s, w, cost])


# TOTAL COST
print("\n==============================")
print("TOTAL COST")
print("Total Cost =", round(pulp.value(model.objective), 2))

results_df = pd.DataFrame(assignments,columns=['Store', 'Warehouse', 'Transport Cost'])

print("\n==============================")
print("RESULT TABLE")
print(results_df)


# SAVE RESULTS TO CSV
results_df.to_csv("facility_location_results.csv",index=False)
print("\nResults saved as facility_location_results.csv")


# CREATE FOLIUM MAP
m = folium.Map(location=[7.0, 80.0],zoom_start=7)

# ADD WAREHOUSE MARKERS
for w in warehouses:
    color = 'red' if w in opened_warehouses else 'gray'
    folium.Marker(location=locations[w],popup=f"Warehouse: {w}",icon=folium.Icon(color=color, icon='home')).add_to(m)

# ADD STORE MARKERS
for s in stores:
    folium.Marker(location=locations[s],popup=f"Store: {s}",icon=folium.Icon(color='blue')).add_to(m)

# DRAW OPTIMAL NETWORK ROUTES
for row in assignments:
    store = row[0]
    warehouse = row[1]
    folium.PolyLine(locations=[locations[warehouse],locations[store]],
        color='green',weight=2).add_to(m)


# SAVE MAP
m.save("facility_network_map.html")
print("\nMap saved as facility_network_map.html")