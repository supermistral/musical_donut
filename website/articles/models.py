from django.db import models
from django.utils import timezone
from django.db.models import Q
import re


class ArticleManager(models.Manager):
    
    def get_queryset(self):
        return super().get_queryset().filter(date_release__lte=timezone.now(), is_active=True)\
            .order_by('-date_release')

    def search(self, query=None):
        queryset = self.get_queryset()
        if query is not None:
            search_lookup = (
                Q(name__icontains=query) |
                Q(image_caption__icontains=query)
            )
            queryset = queryset.filter(search_lookup).distinct()
        return queryset


class TextBlockManager(models.Manager):

    def search(self, query=None):
        queryset = self.get_queryset()
        if query is not None:
            search_lookup = (
                Q(text__icontains=query) |
                Q(song__name__icontains=query) |
                Q(song__genre__name__icontains=query) |
                Q(song__singer__name__icontains=query)
            )
            queryset = queryset.filter(search_lookup).distinct()
        return queryset


class Singer(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Музыкальная группа"
        verbose_name_plural = "Музыкальные группы"


class Genre(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"


class Song(models.Model):
    singer = models.ForeignKey(Singer, on_delete=models.CASCADE, related_name='songs')
    name = models.CharField(max_length=100)
    date_release = models.DateField(null=True, blank=True)
    genre = models.ForeignKey(
        Genre, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='songs'
    )
    is_album = models.BooleanField(default=False)

    ref_vk = models.CharField(max_length=500, blank=True, null=True)
    ref_yandex = models.CharField(max_length=500, blank=True, null=True)
    ref_spotify = models.CharField(max_length=500, blank=True, null=True)
    ref_apple = models.CharField(max_length=500, blank=True, null=True)
    ref_youtube = models.CharField(max_length=500, blank=True, null=True)
    ref_deezer = models.CharField(max_length=500, blank=True, null=True)

    def replace_ref_width(self, ref, height=150):
        if not ref:
            return ref
        regex = re.compile(r' height=\W\d+\W ')
        return regex.sub(f' height="{height}" ', ref)

    def save(self, *args, **kwargs):
        if self.is_album:
            self.ref_yandex = self.replace_ref_width(self.ref_yandex, 500)
            self.ref_spotify = self.replace_ref_width(self.ref_spotify, 500)
            self.ref_apple = self.replace_ref_width(self.ref_apple, 500)
        else:
            self.ref_yandex = self.replace_ref_width(self.ref_yandex)
            self.ref_spotify = self.replace_ref_width(self.ref_spotify)
            self.ref_apple = self.replace_ref_width(self.ref_apple)
        return super().save(*args, **kwargs)

    def __str__(self):
        param_album = "| Альбом" if self.is_album else ""
        return f"{self.singer.name} -> {self.name} {param_album}" 

    class Meta:
        ordering = ['singer__name']
        verbose_name = "Песня"
        verbose_name_plural = "Песни"


class Section(models.Model):
    name = models.CharField(max_length=20, unique=True)
    name_for_url = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name


# Классы блоков для css: center, left, right
# class TextBlockClass(models.Model):
#     name = models.CharField(max_length=20)

#     def __str__(self):
#         return self.name


class TextBlock(models.Model):
    subdivision = models.ForeignKey(
        'Subdivision',
        on_delete=models.CASCADE, 
        related_name="textblocks"
    )
    text = models.TextField()
    slider = models.OneToOneField(
        'ImageSlider',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    # text_class = models.ForeignKey(
    #     TextBlockClass, 
    #     on_delete=models.SET_DEFAULT, 
    #     default="center", 
    #     related_name='textblocks'
    # )
    text_classes_choices = (
        ('center', 'по центру'), 
        ('left', 'текст слева'), 
        ('right', 'текст справа'),
    )
    text_class = models.CharField(max_length=20, choices=text_classes_choices, default='center')

    objects = TextBlockManager()

    def __str__(self):
        temp_name = self.subdivision.name[:30] + ".." if len(self.subdivision.name) > 30 \
            else self.subdivision.name
        temp_text = self.text[:30] + ".." if len(self.text) > 30 else self.text
        return f"{temp_name} -> {temp_text}"

    def save(self, *args, **kwargs):
        self.text = self.text\
            .replace("<ж>", "<b>").replace("</ж>", "</b>")\
            .replace("<к>", "<i>").replace("</к>", "</i>")\
            .replace("<ц>", "<blockquote class='decoration'>").replace("</ц>", "</blockquote>")
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ['subdivision__name']
        verbose_name = "Текстовый блок"
        verbose_name_plural = "Текстовые блоки"


class Article(models.Model):
    name = models.CharField(max_length=100)
    section = models.ForeignKey(
        Section, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='articles'
    )
    image = models.ImageField(
        upload_to='articles',
        default='default/article.jpg',
        blank=True
    )
    slider = models.OneToOneField(
        'ImageSlider', 
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    song = models.ForeignKey(
        Song, 
        on_delete=models.CASCADE, 
        related_name='articles',
        blank=True,
        null=True
    )
    date_release = models.DateTimeField()
    date_change = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    objects = models.Manager()
    ready_objects = ArticleManager()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-date_release']
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"


class Subdivision(models.Model):
    article = models.ForeignKey(
        'Article', 
        on_delete=models.CASCADE, 
        related_name="subdivisions"
    )
    name = models.CharField(max_length=100, blank=True, null=True)
    song = models.ForeignKey(
        Song, 
        on_delete=models.CASCADE, 
        related_name='subdivisions',
        blank=True,
        null=True
    )

    def __str__(self):
        temp_name = self.name[:30] + ".." if len(self.name) > 30 else self.name
        if not temp_name and self.song:
            temp_name = self.song.name
        return f"{self.article.name} -> {temp_name}"

    class Meta:
        ordering = ['article__name']
        verbose_name = "Раздел статьи"
        verbose_name_plural = "Разделы статьи"


class ImageSlider(models.Model):
    name = models.CharField(max_length=50)

    def get_relation(self, str_relation, class_name):
        try:
            obj = class_name.objects.get(slider=self)
            if str_relation:
                str_relation += " | "
            if class_name == TextBlock:
                str_relation += obj.subdivision.name
            else:
                str_relation += obj.name
        except:
            pass
        return str_relation

    def __str__(self):
        obj_relation = ""
        for class_name in [Article, TextBlock]:
            obj_relation = self.get_relation(obj_relation, class_name)
        if not obj_relation:
            obj_relation = "(без привязки)"
        else:
            obj_relation = "| " + obj_relation
        # Дописать для текстблоков
        return f"{self.name} {obj_relation}"

    class Meta:
        ordering = ['name']
        verbose_name = "Слайдер изображений"
        verbose_name_plural = "Слайдеры изображений"


class ImageUnit(models.Model):
    slider = models.ForeignKey(
        ImageSlider, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = models.ImageField(upload_to="sliders")

    def __str__(self):
        first_image = ImageUnit.objects.filter(slider=self.slider).first()
        id_diff = self.id - first_image.id + 1
        return f"{self.slider.name} | {id_diff}"

    class Meta:
        ordering = ['slider__name']
        verbose_name = "Изображение для слайдера"
        verbose_name_plural = "Изображения для слайдера"