from django.contrib import admin
from .models import ItemCategory, Item, Cart, CartItem
from django.contrib import admin
from .models import QuizQuestion, QuizScore

class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'correct_answer')
    list_filter = ('correct_answer',)
    search_fields = ('question_text',)

class QuizScoreAdmin(admin.ModelAdmin):
    list_display = ('username', 'phone_number', 'score', 'date_submitted')
    list_filter = ('date_submitted',)
    search_fields = ('username', 'phone_number')
    ordering = ('-score', '-date_submitted')

admin.site.register(QuizQuestion, QuizQuestionAdmin)
admin.site.register(QuizScore, QuizScoreAdmin)

class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'base_price', 'selling_price', 'source', 'location')
    list_filter = ('category', 'source', 'location')
    search_fields = ('name', 'description', 'source', 'location')

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1

class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'total_amount')
    inlines = [CartItemInline]

admin.site.register(ItemCategory)
admin.site.register(Item, ItemAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem)
