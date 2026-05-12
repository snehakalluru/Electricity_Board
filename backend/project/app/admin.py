from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from django.utils.html import format_html
import os
from datetime import datetime

from .models import Applicant, Connection, Status
from .utils import read_csv_rows, process_rows


class ConnectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'Applicant', 'Load_Applied', 'Date_of_Application', 'Status')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-csv/', self.admin_site.admin_view(self.upload_csv), name='app_connection_upload_csv'),
        ]
        return custom_urls + urls

    def upload_csv(self, request):
        # Preview step: save upload and show dry-run results
        if request.method == 'POST' and 'preview' in request.POST:
            csv_file = request.FILES.get('csv_file')
            if not csv_file:
                messages.error(request, 'No file uploaded')
                return redirect('..')

            upload_dir = os.path.join('..', 'import_uploads')
            os.makedirs(upload_dir, exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d-%H%M%S')
            fname = f'upload-{ts}.csv'
            dest = os.path.join(upload_dir, fname)
            with open(dest, 'wb') as out:
                for chunk in csv_file.chunks():
                    out.write(chunk)

            rows = read_csv_rows(dest)
            stats, log_text, _ = process_rows(rows, do_commit=False)

            sample = rows[:5]
            existing_ids = set(Applicant.objects.values_list('IDNumber', flat=True))
            existing_matches = sum(1 for r in rows if (r.get('ID_Number') or r.get('IDNumber') or r.get('ID')) in existing_ids)

            context = dict(self.admin_site.each_context(request))
            context.update({
                'upload_path': dest,
                'stats': stats,
                'sample': sample,
                'existing_matches': existing_matches,
                'log_preview': log_text.split('\n')[:50],
            })
            return render(request, 'admin/csv_preview.html', context)

        # Confirm/import step
        if request.method == 'POST' and 'import' in request.POST:
            upload_path = request.POST.get('upload_path')
            if not upload_path or not os.path.exists(upload_path):
                messages.error(request, 'Upload not found; please re-upload')
                return redirect('..')

            rows = read_csv_rows(upload_path)
            stats, log_text, log_path = process_rows(rows, do_commit=True, log_dir=os.path.join('..', 'import_logs'))
            messages.success(request, f'Import finished — created applicants: {stats["created_applicants"]}, created connections: {stats["created_connections"]}, updated connections: {stats["updated_connections"]}. Log: {log_path}')
            return redirect('..')

        # GET: show upload form
        context = dict(self.admin_site.each_context(request))
        return render(request, 'admin/csv_upload.html', context)


admin.site.register(Applicant)
admin.site.register(Connection, ConnectionAdmin)
admin.site.register(Status)


def upload_link(obj):
    return format_html('<a class="button" href="upload-csv/">Upload CSV</a>')
