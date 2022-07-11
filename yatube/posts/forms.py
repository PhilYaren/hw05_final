from django import forms
from .models import Follow, Group, Post, Comment


class PostForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea, required=True)
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        empty_label='Разместить пост без группы',
        required=False
    )
    image = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'class':'form-control'}),

        required=False
    )

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    text = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class':'form-control'
            }
        ),
        required=True
    )
    class Meta:
        model = Comment
        fields = ('text',)
