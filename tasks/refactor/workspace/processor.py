import json
def p(d):
    r=[]
    for i in d:
        if i["type"]=="A":
            if i["val"]>10:
                r.append({"n":i["name"],"v":i["val"]*2,"t":"premium_a"})
            else:
                r.append({"n":i["name"],"v":i["val"],"t":"basic_a"})
        elif i["type"]=="B":
            if i["val"]>20:
                r.append({"n":i["name"],"v":i["val"]*1.5,"t":"premium_b"})
            else:
                r.append({"n":i["name"],"v":i["val"],"t":"basic_b"})
        else:
            r.append({"n":i["name"],"v":0,"t":"unknown"})
    return r

def main():
    d=[{"name":"x","type":"A","val":15},{"name":"y","type":"B","val":25},{"name":"z","type":"A","val":5},{"name":"w","type":"C","val":10},{"name":"q","type":"B","val":10}]
    print(json.dumps(p(d)))

if __name__=="__main__":
    main()
