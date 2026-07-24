from django import forms

MAX_CV_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_CV_EXTENSIONS = ("pdf", "txt")


class CVUploadForm(forms.Form):
    cv_file = forms.FileField(
        label="Upload your CV",
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".pdf,.txt"}),
    )

    def clean_cv_file(self):
        cv_file = self.cleaned_data["cv_file"]
        extension = cv_file.name.rsplit(".", 1)[-1].lower() if "." in cv_file.name else ""
        if extension not in ALLOWED_CV_EXTENSIONS:
            raise forms.ValidationError("Please upload a PDF or TXT file.")
        if cv_file.size > MAX_CV_SIZE_BYTES:
            raise forms.ValidationError("File too large — please upload a CV under 5MB.")
        return cv_file
