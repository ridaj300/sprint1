from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from newsapp.models import CustomUser, News, Category, Page, Comments, Subcategory
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import random
from django.utils import timezone
from django.db.models import Q, Count
from textblob import TextBlob

User = get_user_model()

def BASE(request):
    return render(request, 'base.html')


def BASE1(request):
    return render(request, 'base1.html')


def INDEX(request):
    postnews = News.objects.order_by('-posted_date')[:3]
    postnews1 = News.objects.all()[:4]
    category = Category.objects.all()[:4]
    recentnews = News.objects.order_by('-posted_date')[:5]

    context = {
        'postnews': postnews,
        'category': category,
        'recentnews': recentnews,
        'postnews1': postnews1,
    }

    return render(request, 'index.html', context)


def ABOUTUS(request):
    first_page = Page.objects.first()
    context = {
        "page": first_page,
    }
    return render(request, 'aboutus.html', context)


def CONTACTUS(request):
    first_page = Page.objects.first()
    context = {
        "page": first_page,
    }
    return render(request, 'contactus.html', context)


def category_detail(request, id):
    catid = get_object_or_404(Category, id=id)
    news_list = News.objects.filter(cat_id=catid).order_by('-posted_date')
    paginator = Paginator(news_list, 4)

    page_number = request.GET.get('page')
    news = paginator.get_page(page_number)

    return render(request, 'categorywise_newsdetail.html', {'catid': catid, 'news': news})


def VIEW_SINGLENEWS(request, id):
    sinnews = get_object_or_404(News, id=id)
    recentnews = News.objects.order_by('-posted_date')[:4]
    category_counts = Category.objects.annotate(news_count=Count('news'))
    comments_list = Comments.objects.filter(news_id=sinnews, status='Approved')

    if request.method == "POST":
        comment_obj = Comments(
            news_id=sinnews,
            comment=request.POST['comment'],
            name=request.POST['name'],
            email=request.POST['email'],
        )
        comment_obj.save()
        return redirect('thank_you')

    context = {
        "sinnews": sinnews,
        'recentnews': recentnews,
        'category_counts': category_counts,
        'comments_list': comments_list,
    }
    return render(request, 'single-news-details.html', context)


def THANKYOU(request):
    return render(request, 'thankyou.html')


def DASHBOARD(request):
    category_count = Category.objects.count()
    subcategory_count = Subcategory.objects.count()
    news_count = News.objects.count()
    subadmin_count = CustomUser.objects.filter(user_type=2).count()

    sentiments = {
        'Positive': Comments.objects.filter(sentiment='Positive').count(),
        'Negative': Comments.objects.filter(sentiment='Negative').count(),
        'Neutral': Comments.objects.filter(sentiment='Neutral').count(),
    }

    comments = Comments.objects.all()  # Fetch all comments for sentiment table

    context = {
        'category_count': category_count,
        'subcategory_count': subcategory_count,
        'news_count': news_count,
        'subadmin_count': subadmin_count,
        'sentiments': sentiments,
        'comments': comments,  # Add comments data to the dashboard context
    }

    return render(request, 'dashboard.html', context)


def LOGIN(request):
    return render(request, 'login.html')


def doLogin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            if remember_me:
                request.session.set_expiry(2592000)
            else:
                request.session.set_expiry(0)

            user_type = user.user_type
            if user_type == '1':
                return redirect('dashboard')
            elif user_type == '2':
                return redirect('dashboard')
        else:
            messages.error(request, 'Email or Password is not valid')
            return render(request, 'login.html', {'username': username, 'remember_me': remember_me})
    else:
        messages.error(request, 'Invalid request method')
        return redirect('login')


def doLogout(request):
    logout(request)
    return redirect('login')


@login_required(login_url='/')
def ADMIN_PROFILE(request):
    user = CustomUser.objects.get(id=request.user.id)
    context = {
        "user": user,
    }
    return render(request, 'profile.html', context)


@login_required(login_url='/')
def ADMIN_PROFILE_UPDATE(request):
    if request.method == "POST":
        profile_pic = request.FILES.get('profile_pic')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        username = request.POST.get('username')

        try:
            customuser = CustomUser.objects.get(id=request.user.id)
            customuser.first_name = first_name
            customuser.last_name = last_name

            if profile_pic is not None and profile_pic != "":
                customuser.profile_pic = profile_pic
            customuser.save()
            messages.success(request, "Your profile has been updated successfully")
            return redirect('admin_profile')
        except:
            messages.error(request, "Your profile update has failed")
    return render(request, 'profile.html')


@login_required(login_url='/')
def CHANGE_PASSWORD(request):
    context = {}
    ch = User.objects.filter(id=request.user.id)

    if len(ch) > 0:
        data = User.objects.get(id=request.user.id)
        context["data"] = data
    if request.method == "POST":
        current = request.POST["cpwd"]
        new_pas = request.POST['npwd']
        user = User.objects.get(id=request.user.id)
        un = user.username
        check = user.check_password(current)
        if check:
            user.set_password(new_pas)
            user.save()
            messages.success(request, 'Password changed successfully!')
            user = User.objects.get(username=un)
            login(request, user)
        else:
            messages.error(request, 'Current password is incorrect!')
            return redirect("change_password")
    return render(request, 'change-password.html')


def SEARCH_NEWS(request):
    if request.method == "GET":
        query = request.GET.get('query', '')
        if query:
            searchnews = News.objects.filter(
                Q(posttitle__icontains=query) |
                Q(cat_id__catname__icontains=query) |
                Q(subcategory_id__subcatname__icontains=query)
            )

            if searchnews.exists():
                messages.info(request, "Search results for: " + query)
            else:
                messages.info(request, "No records found for: " + query)

            paginator = Paginator(searchnews, 10)
            page = request.GET.get('page', 1)

            try:
                searchnews_paginated = paginator.page(page)
            except PageNotAnInteger:
                searchnews_paginated = paginator.page(1)
            except EmptyPage:
                searchnews_paginated = paginator.page(paginator.num_pages)

            return render(request, 'search-news.html', {
                'searchnews': searchnews_paginated,
                'query': query,
            })
        else:
            return render(request, 'search-news.html', {})


# Perform Sentiment Analysis
def perform_sentiment_analysis(request):
    if request.method == "POST":
        # Dictionary to store sentiment analysis results for each news article
        news_sentiments = {}

        # Analyze all news articles
        news_articles = News.objects.all()

        for news in news_articles:
            # Fetch all comments related to the current news article
            comments = Comments.objects.filter(news_id=news.id)
            positive_count = 0
            negative_count = 0
            neutral_count = 0

            for comment in comments:
                if comment.comment.strip():  # Ensure the comment is not empty
                    try:
                        analysis = TextBlob(comment.comment)  # Perform sentiment analysis
                        polarity = analysis.sentiment.polarity
                        # Determine sentiment based on polarity
                        if polarity > 0:
                            positive_count += 1
                            comment.sentiment = 'Positive'
                        elif polarity < 0:
                            negative_count += 1
                            comment.sentiment = 'Negative'
                        else:
                            neutral_count += 1
                            comment.sentiment = 'Neutral'
                        comment.save()  # Save updated sentiment in the database
                    except Exception as e:
                        # Handle any analysis errors gracefully
                        messages.error(request, f"Error analyzing comment ID {comment.id}: {e}")
                else:
                    messages.warning(request, f"Comment ID {comment.id} is empty and was skipped.")

            # Save aggregated sentiment data for the current news article
            news_sentiments[news.id] = {
                'title': news.posttitle,  # Replace with appropriate field for the news title
                'positive': positive_count,
                'negative': negative_count,
                'neutral': neutral_count,
            }

        # Save sentiment data in session for display on the dashboard
        request.session['news_sentiments'] = news_sentiments
        messages.success(request, "Sentiment analysis completed successfully.")
        return redirect('dashboard')  # Ensure an HttpResponse is returned

    # Handle invalid request methods
    messages.error(request, "Invalid request method.")
    return redirect('dashboard')  # Redirect to dashboard in case of invalid requests
