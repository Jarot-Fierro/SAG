# from django import forms
#
# from core.models import Funcionario
# from soporte.models import Ticket
#
#
# class FormTicket(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)
#
#         if not self.instance.pk:
#             self.fields['area_soporte'].initial = 'INFORMATICA'
#
#         if self.instance and self.instance.funcionario_id:
#             self.fields['funcionario'].queryset = Funcionario.objects.filter(id=self.instance.funcionario_id)
#         else:
#             self.fields['funcionario'].queryset = Funcionario.objects.none()
#
#     titulo = forms.CharField(
#         label='Título del problema',
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Ej: Problema con impresora'
#         }),
#         required=True
#     )
#
#     nombre_funcionario = forms.CharField(
#         label='Nombre del funcionario',
#         widget=forms.TextInput(attrs={
#             'class': 'form-control form-control-sm',
#         }),
#         required=True
#     )
#
#     nombre_servicio = forms.CharField(
#         label='Nombre del servicio',
#         widget=forms.TextInput(attrs={
#             'class': 'form-control form-control-sm',
#         }),
#         required=True
#     )
#
#     correo_funcionario = forms.CharField(
#         label='Correo del funcionario',
#         widget=forms.TextInput(attrs={
#             'class': 'form-control form-control-sm',
#         }),
#         required=True
#     )
#
#     descripcion = forms.CharField(
#         label='Descripción del problema',
#         widget=forms.Textarea(attrs={
#             'class': 'form-control',
#             'rows': 4,
#             'placeholder': 'Describa el problema que está presentando'
#         }),
#         required=False
#     )
#
#     area_soporte = forms.ChoiceField(
#         label='Área de soporte',
#         choices=[('MANTENCION', 'Mantencion'), ('INFORMATICA', 'Informatica')],
#         widget=forms.Select(attrs={
#             'class': 'form-control'
#         }),
#         required=True
#     )
#
#     funcionario = forms.ModelChoiceField(
#         label='Funcionario solicitante',
#         queryset=Funcionario.objects.none(),
#         widget=forms.Select(attrs={
#             'class': 'form-control select2-ajax',
#             'data-ajax-url': '/funcionario/buscar-funcionario-ajax/'
#         }),
#         required=True
#     )
#
#     class Meta:
#         model = Ticket
#         fields = [
#             'titulo',
#             'funcionario',
#             'nombre_funcionario',
#             'correo_funcionario',
#             'nombre_servicio',
#             'area_soporte',
#             'descripcion',
#         ]
