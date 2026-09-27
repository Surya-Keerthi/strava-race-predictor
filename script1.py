names=input("What is your name?")
list_ages=[]
list_names=[]
print(list_names)
while names != 'stop':
    ages=input("What is your age?")
    list_ages.append(ages)
    print(list_ages)
    if ages != -1:
        names=input("What is your name?")
        list_names.append(names)
        print(list_names)

max_age= max(list_ages)
print("The highest age is", max_age)