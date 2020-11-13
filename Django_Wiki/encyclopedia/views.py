from django.shortcuts import render, redirect
from django.urls import reverse
import random
from django.http import HttpResponseRedirect


from . import util
import markdown2

pagelists = util.list_entries()
pagelists_co = []
for pagelist in pagelists:
    pagelists_co.append(pagelist.lower())

#default page
def index(request):
    return render(request, "encyclopedia/index.html", {
        "entries": util.list_entries()
    })

#render a page that displays the contents of that encyclopedia entry.
def wiki(request, title):
    pagelists = util.list_entries()
    pagelists_co = []
    for pagelist in pagelists:
        pagelists_co.append(pagelist.lower())

    if title.lower() in pagelists_co:
        content = util.get_entry(title)
        return render(request, "encyclopedia/page.html", {
            "title": title,
            "content": markdown2.markdown(content) #covert markdown to html
        })
    else:
        return render(request, "encyclopedia/error.html", {
            "error": "The page you request is not found."
        })

#search function
def search(request):
    if request.method == "POST":
        title = request.POST
        title = title['q']
        
        pagelists_co = []
        for pagelist in pagelists:
            pagelists_co.append(pagelist.lower())

        if title.lower() in pagelists_co:
            content = util.get_entry(title)
            return render(request, "encyclopedia/page.html", {
                "title": title.lower(),
                "content": markdown2.markdown(content) #covert markdown to html
            })

        searchlists = []
        for pagelist in pagelists:
            if title.lower() in pagelist.lower():
                searchlists.append(pagelist)
        
        if not searchlists:
            return render(request, "encyclopedia/error.html", {
                "error": "The page you request is not found."
            })
        else:
            return render(request, "encyclopedia/search.html", {
                "searchlists": searchlists
            })
    else:
        #redirect to the index page
        return HttpResponseRedirect(reverse("index"))
    

#Create New Page
def add_page(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        if title.lower() in pagelists_co:  
            return render(request, "encyclopedia/add.html", {
                'exist': True,
                'title': title
            })
        else: 
            util.save_entry(title, content)
            return redirect(wiki, title=title)
    else:
        return render(request, "encyclopedia/add.html", {
            'exist': False
        })

#Edit Page
def edit_page(request, title):
    if request.method == 'GET':
        content = util.get_entry(title)
        return render(request, "encyclopedia/edit.html", {
            'title': title,
            'content': content
    })
    else:
        content = request.POST.get('content')
        util.save_entry(title, content)
        return redirect(wiki, title=title)
    
#Get random page
def random_page(request):
    random_title = random.randint(0, len(pagelist)-1)
    title = pagelists[random_title]
    return redirect(wiki, title=title)
    
   



