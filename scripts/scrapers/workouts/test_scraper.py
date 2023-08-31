import pandas as pd
from random import randint

# pdf = pd.read_csv("data/workoutlinks/full_male_workout_links.csv")
# pdf.Links = pdf.Links.apply(eval)
# links = list(pdf.Links)

# probelm_links = []
# for index, link_list in enumerate(links):
#     if index <= 225:
#         continue
#     num_links = len(link_list)
#     rand_index = randint(0, len(link_list) - 1)
#     link = link_list[rand_index]
#     print(f"Processing link: {rand_index} of list: {index}, link: {link}")
#     try:
#         scrape_workout_page(link)
#     except Exception as e:
#         print(e, e.__str__())
#         probelm_links.append((link, e.__str__()))


tests = [
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/coachdmurph/5bf3ec42176a3027b0ad04d8",
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/zzyt/5721ad540cf2b58f38ced9d7",
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/zzupan90/5428c1e70cf2bb28d5a57422",
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/zzneo/5bcad0494e400527ce7156fc",
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/zzohaib/5376f2f70cf28afcb6ce2e9a",
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/-NYSE1-/4fb56f36b488e39f44f45352",
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/zzshad/593210b4af19ce69876e7dcd",
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/zzolowicz/5901402f36d69c3acb773dd4",
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/12LittLebit/5a024d9fb36829286bb464e9",
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/12laynew/58097f260cf27a6fb6996c8d"
]

# for test in tests:
#     print(f"Processing link: {test}")
#     try:
#         scrape_workout_page(test)
#     except Exception as e:
#         print(e, e.__str__())


start = time.time()
workout = scrape_workout_page(
    tests[9]
)
print(f"Time taken: {time.time() - start}")


with open("./data/workout.json", "w") as f:
    f.write(json.dumps(workout, indent=4))

# To Do
# - Make sure tests pass
# - Finish this
