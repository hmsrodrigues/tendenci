from django.db import models
from django.core.urlresolvers import reverse
from embedly import get_oembed

from perms.models import TendenciBaseModel
from tinymce import models as tinymce_models
from video.managers import VideoManager

class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(unique=True)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def get_absolute_url(self):
        return reverse('video-category', args=[self.slug])
    
class Video(TendenciBaseModel):
    """
    Video plugin to add embedding based on video url. Uses embed.ly
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category)
    image = models.ImageField(upload_to='uploads/video/%y/%m', blank=True)
    video_url = models.CharField(max_length=500, help_text='Youtube, Vimeo, etc..')
    description = tinymce_models.HTMLField()
    
    objects = VideoManager()
    
    def __unicode__(self):
        return self.title
    
    class Meta:
        permissions = (("view_video","Can view video"),)
    
    @models.permalink
    def get_absolute_url(self):
        return ("video-details", [self.slug])
    
    def embed_code(self):
        return get_oembed_code(self.video_url, 600, 400)


class OembedlyCache(models.Model):
    "For better performance all oemed queryes are cached in this model"
    url = models.CharField(max_length=800)
    width = models.IntegerField(db_index=True)
    height = models.IntegerField(db_index=True)
    code = models.TextField()
    
    def __unicode__(self):
        return self.url
    
    @staticmethod    
    def get_code(url, width, height):
        try:
            return OembedlyCache.objects.filter(url=url, width=width, height=height)[0].code
        except IndexError:
            try:
                result = get_oembed(url, format='json', maxwidth=width, maxheight=height)
                code = result['html']
            except KeyError:
                return 'Unable to embed code for video <a href="%s">%s</a>' % (url, url)
            except Exception, e:
                return 'Unable to embed code for video <a href="%s">%s</a><br>Error: %s' % (url, url, e) 
            obj = OembedlyCache(url=url, width=width, height=height, code=code)
            obj.save()
            return code

def get_oembed_code(url, width, height):
    return OembedlyCache.get_code(url, width, height)
