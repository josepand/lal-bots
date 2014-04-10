import pickle
import datetime

with open('pokerdb.dat','r+') as f1:
    with open('pokerdb_new.dat','w') as f2:
        data = pickle.load(f1)
        data2 = {}
        for pl,ch in data.iteritems():
            data2.update({pl:{'chips':ch,
                              'last_rebuy':datetime.date(2013,12,10)}})
        pickle.dump(data2,f2)