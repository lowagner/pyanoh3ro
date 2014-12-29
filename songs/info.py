import pickle

settings={}

settings["Piece"]="C scale"
settings["PlayerStarts"]=True

with open("info.pkl", 'wb') as handle:
    pickle.dump(settings, handle)
