import time, requests, bz2, flask, flask_restful, threading
from flask_restful import Resource
newlist = []
custom = ['http://julioverne.github.io/Packages.bz2','https://repo.auxiliumdev.com/Packages.bz2','https://jacc.github.io/repo/Packages.bz2','http://cydia.r333d.com/Packages.bz2','http://tateu.net/repo/Packages.bz2','https://paxcex.github.io/Packages.bz2','https://antiquebeta.github.io/Packages.bz2','http://rpetri.ch/repo/Packages.bz2','https://repo.applebetas.co/Packages.bz2', 'https://cydia.angelxwind.net/Packages.bz2', 'https://repo.dynastic.co/Packages.bz2', "https://repo.packix.com/Packages.bz2", 'https://repo.chariz.io/Packages.bz2', "https://yakz.cf/Packages.bz2"]
# Not sure why these are separate actually, might have helped with a benefit of being first/last some point in time...
sources = ['http://apt.saurik.com/cydia/Packages.bz2', 'http://apt.modmyi.com/dists/stable/main/binary-iphoneos-arm/Packages.bz2', 'http://apt.thebigboss.org/repofiles/cydia/dists/stable/main/binary-iphoneos-arm/Packages.bz2', 'http://zodttd.saurik.com/repo/cydia/dists/stable/main/binary-iphoneos-arm/Packages.bz2']
def longe():
    global custom
    global sources
    global newlist
    # Moved sources to globals for a planned add_source endpoint
    nlst = []

    # Goes through every source
    for source in custom + sources:
        print("Loading database {}...".format(source.split("//")[1].split("/")[0]))
        try:
            # Gets source's Packages.bz2 file (Note: add support for less used Packages.gz format as well.)
            data = requests.get(source)
        except requests.exceptions.ConnectionError:
            print("Error: {} had a serious connection issue.".format(source))
            continue
        # Fuck you ryley angus, this is because of your rate limits

        print("Splitting package list...")
        try:
            listing = bz2.decompress(data.content).decode('utf-8', 'ignore').splitlines()
            # Decompresses packages file and splits it into individual lines.
        except:
            print("Error: {} had a serious error.".format(source))
            continue

        print("Parsing list...")
        # This section is weird as fuck

        

        gl = {}
        # Goes through every single line. gl is the current tweak dictionary being made, x is the current line, and listing is all the lines.
        for x in listing:
            if x != "": # Checks for the empty line between all Package entries
                try:
                    if x.endswith(":") or x.endswith(": "): # Some lines have no value (e.g. "Sponsor: ")
                        x = x + " "
                    gl[x.split(": ")[0]] = ": ".join(x.split(": ")[1:]) # x.split(": ") will usually return a list with 2 items, as most lines are formatted like "Maintainer: Yak". 
                    # The above line basically makes gl into {'Package':'com.oganessiumspkgid.appballs','Name':'Appballs'} etc. The .join thing is incase the value has a colon in it

                    # This part was mind fucking to do. It just formats lines with values like "Yak <yaksemail@yakz.cf>" into {'Name':'Yak','Email':'yaksemail@yakz.cf'}
                    try:
                        if (x.split(": ")[0] == "Maintainer" or x.split(": ")[0] == "Sponsor" or x.split(": ")[0] == "Author"):
                            if len(x.split(" <")) > 1:
                                gl[x.split(": ")[0]] = {'Name':": ".join(x.split(": ")[1:]).split(" <")[0],'Email': ": ".join(x.split(": ")[1:]).split(" <")[1].split(">")[0]}
                    except:
                        print("errror {} {}".format(x, gl))
                    if x.split(": ")[0] == "Pre-Depends" or x.split(": ")[0] == "Provides" or x.split(": ")[0] == "Depends" or x.split(": ")[0] == "Replaces" or x.split(": ")[0] == "Conflicts":
                        gl[x.split(": ")[0]] = x.split(': ', 1)[1].split(", ")
                    if x.split(": ")[0] == "Tag":
                        gl[x.split(": ")[0]] = {m[0]:m[1] for m in [n.split("::") for n in x.split(": ", 1)[1].split(", ")]}
                except:
                    try:
                        gl[list(gl.keys())[-1]] = gl[list(gl.keys())[-1]] + x
                    except:
                        pass
                    
            else:
                # This part essentially packages gl into a list called nlst. nlst will later be incorporated into newlist.
                gl['repo'] = source.split("//")[1].split("/")[0]
                if source in sources:
                    gl['Icon'] = "http://cydia.saurik.com/icon@2x/{}.png".format(gl['Package'])
                else:
                    gl['Icon'] = None
                if gl=={}:
                    continue
                nlst.append(gl)
                gl={}
    newlist = nlst
    time.sleep(300) # so it's 5 minutes. yall can lower this
    longe()

app = flask.Flask(__name__, template_folder='files')
api = flask_restful.Api(app)
# creates flask app (do i need to comment this part??)


download_thread = threading.Thread(target=longe) # Longe is the function. Why longe? I don't fucking know
download_thread.start()
# threads the repo updater in the background. it's called download_thread because i copy pasted it from stackoverflow

class Tweak(Resource): # Main flask resource, q = search query
    def get(self, q):
        global newlist
        if bool(flask.request.args.get('comfy')):
            comfy=True
        else:
            comfy=False
        results = {}

        exact = {}
        starts1 = {}
        starts2 = {}
        in1 = {}
        in2 = {}

        for x in newlist:
            if len(exact) + len(starts1) + len(starts2) + len(in1) + len(in2) >= 100: #Stops if results over 100 to save time/space
                break
            try:
                # This right here is how the packages are organized. Not sure what results does. starts1 is if the search term starts with the tweak name, starts2 is if the tweak name starts with the search term, in1 is if the search term text is in the tweak name and in2 is if the tweak name is in the search text.
                # Each dictionary is formatted like {'com.oganessiumspkgid.brenskin':{'Name':'brenskin':'Version':'0.69'}}
                if q.lower() in x['Name'].lower() or x['Name'].lower().startswith(q.lower()) or q.lower().startswith(x['Name'].lower()):
                    results[x['Package']] = x
                if q.lower() == x['Name'].lower() or q.lower() == x['Package'].lower():
                    exact[x['Package']] = x
                elif q.lower().startswith(x['Name'].lower()) or q.lower().startswith(x['Package'].lower()):
                    starts1[x['Package']] = x
                elif x['Name'].lower().startswith(q.lower()) or x['Package'].lower().startswith(q.lower()):
                    starts2[x['Package']] = x
                elif q.lower() in x['Name'].lower() or q.lower() in x['Package'].lower():
                    in1[x['Package']] = x
                elif x['Name'].lower() in q.lower() or x['Package'].lower() in q.lower():
                    in2[x['Package']] = x
                else:
                    pass
            except:
                # If the tweak has no name (e.g. adv-cmds)
                try:
                    if q.lower() == x['Package'].lower():
                        exact[x['Package']] = x
                    elif q.lower().startswith(x['Package'].lower()):
                        starts1[x['Package']] = x
                    elif q.lower() in x['Package'].lower():
                        in1[x['Package']] = x
                    elif x['Package'].lower() in q.lower():
                        in2[x['Package']] = x
                    else:
                        pass
                except Exception as e:
                    continue


        trueResults = []


        # Converts the four separate dicts into one list of tweaks (trueResults)



        for k, v in exact.items():
            trueResults.append(v)
        for k, v in starts1.items():
            trueResults.append(v)
        for k, v in starts2.items():
            trueResults.append(v)
        for k, v in in1.items():
            trueResults.append(v)
        for k, v in in2.items():
            trueResults.append(v)

        # Formats as comfy
        if comfy==True:
            for a in trueResults:
                comf = {}
                comf['id'] = a['Package']
                comf['name'] = a['Name']
                try:
                    comf['desc'] = a['Description']
                except:
                    comf['desc'] = None
                comf['version'] = a['Version']
                try:
                    comf['author'] = a['Author']['Name']
                except:
                    try:
                        comf['author'] = a['Author']
                    except:
                        pass
                try:
                    comf['maintainer'] = a['Maintainer']['Name']
                except:
                    try:
                        comf['maintainer'] = a['Maintainer']
                    except:
                        pass
                try:
                    comf['depic'] = a['depic']
                except:
                    pass
                comf['section'] = a['Section']
                comf['file'] = a['Filename']
                comf['icon'] = a['Icon']
                try:
                    comf['depends'] = a['Depends']
                except:
                    pass
                comf['repo'] = a['repo']
                trueResults[trueResults.index(a)] = comf

        # need a better way to do this
        #result limit
        if str(flask.request.args.get('limit')).isdigit():
            trueResults = trueResults[:int(flask.request.args.get('limit'))]



        # Returns the final list
        return trueResults, 200




api.add_resource(Tweak, '/<string:q>')

@app.route("/")
def root():
    return flask.render_template('index.html')
    # Generates files/index.html

app.run(host="127.0.0.1", debug=True, port=int("80")) # launches server
