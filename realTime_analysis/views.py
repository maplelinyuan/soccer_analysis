from django.shortcuts import render
from realTime_analysis.models import SingleMatch
from django.shortcuts import render

# Create your views here.
def index(request):
    # temp = loader.get_template('teams_rate/index.html')
    # return HttpResponse(temp.render())
    match_list = SingleMatch.objects.all()
    context = {'match_list': match_list}
    return render(request, 'realTime_analysis/index.html', context)

def match(request):
    return render(request, 'realTime_analysis/match.html')
