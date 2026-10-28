import bpy
result={}
for name in ['05_Slow_Cooked_Meat_Pieces','06_Torn_Meat_Fibers','07_Gelatinous_Fat_Seams']:
    ob=bpy.data.objects[name]
    adj=[[] for _ in ob.data.vertices]
    for e in ob.data.edges:
        a,b=e.vertices;adj[a].append(b);adj[b].append(a)
    seen=set();sizes=[]
    for i in range(len(adj)):
        if i in seen:continue
        seen.add(i);stack=[i];count=0
        while stack:
            v=stack.pop();count+=1
            for j in adj[v]:
                if j not in seen:seen.add(j);stack.append(j)
        sizes.append(count)
    result[name]={'components':len(sizes),'first_sizes':sizes[:32],'size_counts':{str(s):sizes.count(s) for s in set(sizes)}}
