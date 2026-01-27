from django.urls import path
from . import views

urlpatterns = [
    path('', views.IndexPage.as_view(), name='index'),
    path('login/', views.LoginPage.as_view(), name='login'),
    path('logout/', views.LogoutPage.as_view(), name='logout'),
    path('signup/', views.RegisterPage.as_view(), name='register'),
    path('lost-password/', views.LostPasswordPage.as_view(), name='lost-password'),
    path('restore-password/', views.RestorePasswordPage.as_view(), name='restore-password'),
    path('verify/', views.VerifyPage.as_view(), name='verify'),
    path('account/', views.AccountPage.as_view(), name='account'),
    path('pricing/', views.PricingPage.as_view(), name='pricing'),
    path('checkout/', views.CheckoutPage.as_view(), name='checkout'),
    path('contact/', views.ContactPage.as_view(), name='contact'),
    path('about/', views.AboutPage.as_view(), name='about'),
    path('terms/', views.TermsPage.as_view(), name='terms'),
    path('privacy/', views.PrivacyPage.as_view(), name='privacy'),
    path('refund/', views.RefundPage.as_view(), name='refund'),
    path('success/', views.SuccessPage.as_view(), name='success'),
    path('cancel/', views.CancelSubscriptionPage.as_view(), name='cancel'),
    path('delete-account/', views.DeleteAccountPage.as_view(), name='delete'),
    path('how-it-works/', views.HowItWorksPage.as_view(), name='how-it-works'),
    path('examples/', views.ExamplesPage.as_view(), name='examples'),
    path('tutorials/', views.TutorialsPage.as_view(), name='tutorials'),
    path('faq/', views.FAQPage.as_view(), name='faq'),

    # Use Case Landing Pages (SEO)
    path('for/content-creators/', views.UseCase_ContentCreators.as_view(), name='usecase-content-creators'),
    path('for/educators/', views.UseCase_Educators.as_view(), name='usecase-educators'),
    path('for/game-developers/', views.UseCase_GameDev.as_view(), name='usecase-gamedev'),
    path('for/artists/', views.UseCase_Artists.as_view(), name='usecase-artists'),

    # Feature Pages (SEO)
    path('features/ai-pose-detection/', views.Feature_PoseDetection.as_view(), name='feature-pose-detection'),
    path('features/motion-presets/', views.Feature_MotionPresets.as_view(), name='feature-motion-presets'),
    path('features/export-formats/', views.Feature_ExportFormats.as_view(), name='feature-export-formats'),

    # API Documentation
    path('api/docs/', views.APIDocsPage.as_view(), name='api-docs'),

    # Sitemap
    path('sitemap.xml', views.SitemapView.as_view(), name='sitemap'),
    path('robots.txt', views.RobotsTxtView.as_view(), name='robots'),
]
