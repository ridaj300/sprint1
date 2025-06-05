from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from textblob import TextBlob
from .models import Comments

# Admin action to analyze sentiments
@admin.action(description="Analyze Sentiments for Selected Comments")
def analyze_sentiments(modeladmin, request, queryset):
    for comment in queryset:
        analysis = TextBlob(comment.comment)  # Perform sentiment analysis on the comment text
        polarity = analysis.sentiment.polarity  # Get the polarity score
        if polarity > 0:
            comment.sentiment = 'Positive'
        elif polarity < 0:
            comment.sentiment = 'Negative'
        else:
            comment.sentiment = 'Neutral'
        comment.save()  # Save the sentiment label
    modeladmin.message_user(request, "Sentiment analysis completed successfully.")

# Custom admin page view
def sentiment_analysis_view(request):
    # Prepare sentiment data for rendering
    sentiments = {
        'Positive': Comments.objects.filter(sentiment='Positive').count(),
        'Negative': Comments.objects.filter(sentiment='Negative').count(),
        'Neutral': Comments.objects.filter(sentiment='Neutral').count(),
    }
    return render(request, 'includes1/sentiment_analysis.html', {'sentiments': sentiments})

# Admin customization
@admin.register(Comments)
class CommentsAdmin(admin.ModelAdmin):
    list_display = ('comment', 'name', 'email', 'sentiment', 'posted_date')  # Fields to display in admin
    list_filter = ('sentiment',)  # Enable filtering by sentiment
    search_fields = ('comment', 'name', 'email')  # Add search functionality
    actions = [analyze_sentiments]  # Add custom admin action

# Custom admin site
class CustomAdminSite(admin.AdminSite):
    site_header = "News Portal Admin"
    site_title = "News Portal Admin Dashboard"
    index_title = "Welcome to News Portal Admin"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('sentiment-analysis/', sentiment_analysis_view, name='sentiment_analysis'),
        ]
        return custom_urls + urls

# Instantiate the custom admin site
admin_site = CustomAdminSite(name='custom_admin')
