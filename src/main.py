from tcrap import tCrap

if __name__ == "__main__":
    try :
        tCrap().run()
    except Exception as err:
        print("[Error]{}".format(err))
