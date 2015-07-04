from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from common.forms import DetailForm

from .models import (
    Document, DocumentType, DocumentPage, DocumentTypeFilename
)
from .literals import DEFAULT_ZIP_FILENAME
from .widgets import DocumentPagesCarouselWidget, DocumentPageImageWidget


# Document page forms
class DocumentPageForm(DetailForm):
    class Meta:
        fields = ()
        model = DocumentPage

    def __init__(self, *args, **kwargs):
        zoom = kwargs.pop('zoom', 100)
        rotation = kwargs.pop('rotation', 0)
        super(DocumentPageForm, self).__init__(*args, **kwargs)
        self.fields['page_image'].initial = self.instance
        self.fields['page_image'].widget.attrs.update({
            'zoom': zoom,
            'rotation': rotation
        })

    page_image = forms.CharField(
        label=_('Page image'), widget=DocumentPageImageWidget()
    )


# Document forms


class DocumentPreviewForm(forms.Form):
    def __init__(self, *args, **kwargs):
        document = kwargs.pop('document', None)
        super(DocumentPreviewForm, self).__init__(*args, **kwargs)
        self.fields['preview'].initial = document
        try:
            self.fields['preview'].label = _('Document pages (%d)') % document.page_count
        except AttributeError:
            self.fields['preview'].label = _('Document pages (%d)') % 0

    preview = forms.CharField(widget=DocumentPagesCarouselWidget())


class DocumentForm(forms.ModelForm):
    """
    Form sub classes from DocumentForm used only when editing a document
    """
    class Meta:
        model = Document
        fields = ('label', 'description', 'language')

    def __init__(self, *args, **kwargs):
        document_type = kwargs.pop('document_type', None)

        super(DocumentForm, self).__init__(*args, **kwargs)

        # Is a document (documents app edit) and has been saved (sources app upload)?
        if self.instance and self.instance.pk:
            document_type = self.instance.document_type

        filenames_qs = document_type.filenames.filter(enabled=True)
        if filenames_qs.count():
            self.fields['document_type_available_filenames'] = forms.ModelChoiceField(
                queryset=filenames_qs,
                required=False,
                label=_('Quick document rename'))


class DocumentPropertiesForm(DetailForm):
    """
    Detail class form to display a document file based properties
    """
    class Meta:
        fields = ('document_type', 'description', 'language')
        model = Document


class DocumentTypeSelectForm(forms.Form):
    """
    Form to select the document type of a document to be created, used
    as form #1 in the document creation wizard
    """
    document_type = forms.ModelChoiceField(queryset=DocumentType.objects.all(), label=('Document type'))


class PrintForm(forms.Form):
    page_range = forms.CharField(label=_('Page range'), required=False)


class DocumentTypeForm(forms.ModelForm):
    """
    Model class form to create or edit a document type
    """
    class Meta:
        fields = ('name', 'trash_time_period', 'trash_time_unit', 'delete_time_period', 'delete_time_unit')
        model = DocumentType


class DocumentTypeFilenameForm(forms.ModelForm):
    """
    Model class form to edit a document type filename
    """
    class Meta:
        fields = ('filename', 'enabled')
        model = DocumentTypeFilename


class DocumentTypeFilenameForm_create(forms.ModelForm):
    """
    Model class form to create a new document type filename
    """
    class Meta:
        fields = ('filename',)
        model = DocumentTypeFilename


class DocumentDownloadForm(forms.Form):
    compressed = forms.BooleanField(label=_('Compress'), required=False, help_text=_('Download the document in the original format or in a compressed manner.  This option is selectable only when downloading one document, for multiple documents, the bundle will always be downloads as a compressed file.'))
    zip_filename = forms.CharField(initial=DEFAULT_ZIP_FILENAME, label=_('Compressed filename'), required=False, help_text=_('The filename of the compressed file that will contain the documents to be downloaded, if the previous option is selected.'))

    def __init__(self, *args, **kwargs):
        self.document_versions = kwargs.pop('document_versions', None)
        super(DocumentDownloadForm, self).__init__(*args, **kwargs)
        if len(self.document_versions) > 1:
            self.fields['compressed'].initial = True
            self.fields['compressed'].widget.attrs.update({'disabled': True})
