

def extract_heads_array():
    hds = flopy.utils.HeadFile("freyberg6_freyberg.hds")
    for it,t in enumerate(hds.get_times()):
        d = hds.get_data(totim=t)
        for k,dlay in enumerate(d):
            np.savetxt("hdslay{0}_t{1}.txt".format(k+1,it+1),d[k,:,:],fmt="%15.6E")

    lst = flopy.utils.Mf6ListBudget("freyberg6.lst")
    inc,cum = lst.get_dataframes(diff=True,start_datetime=None)
    inc.columns = inc.columns.map(lambda x: x.lower().replace("_","-"))
    cum.columns = cum.columns.map(lambda x: x.lower().replace("_", "-"))
    inc.index.name = "totim"
    cum.index.name = "totim"
    inc.to_csv("inc.csv")
    cum.to_csv("cum.csv")
    return


    hds = gwf.output.head() # get handle to binary head file
    head = hds.get_data() # get the head data from the file