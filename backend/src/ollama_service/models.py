from django.db import models

class ModelFamily(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Capability(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class QuantizationLevel(models.Model):
    level = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.level

class LLMModel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    model = models.CharField(max_length=100)
    modified_at = models.DateTimeField()
    size = models.BigIntegerField()
    digest = models.CharField(max_length=64)

class LLMModelDetails(models.Model):
    llm_model = models.OneToOneField(LLMModel, on_delete=models.CASCADE, related_name='details')
    parent_model = models.ForeignKey(LLMModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='child_models')
    format = models.CharField(max_length=50, blank=True, null=True)
    family = models.ForeignKey(ModelFamily, on_delete=models.SET_NULL, null=True, blank=True)
    families = models.ManyToManyField(ModelFamily, related_name='variants', blank=True)
    parameter_size = models.CharField(max_length=20, blank=True, null=True)
    quantization = models.ForeignKey(QuantizationLevel, on_delete=models.SET_NULL, null=True, blank=True)

class LLMModelCapability(models.Model):
    llm_model = models.ForeignKey(LLMModel, on_delete=models.CASCADE, related_name='capabilities')
    capability = models.ForeignKey(Capability, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('llm_model', 'capability')