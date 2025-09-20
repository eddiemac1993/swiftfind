from django.shortcuts import render

def request_ride(request):
    return render(request, 'taxi/request_ride.html')
