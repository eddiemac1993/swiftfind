from django.shortcuts import render

def track_order(request):
    return render(request, 'tracking/track_order.html')
