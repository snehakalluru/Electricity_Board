import csv
import os
from datetime import datetime
from django.db import transaction
from django.utils import timezone

from .models import Applicant, Connection, Status


def read_csv_rows(path):
    # Try utf-8, fall back to cp1252
    try:
        with open(path, newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    except UnicodeDecodeError:
        with open(path, newline='', encoding='cp1252') as f:
            return list(csv.DictReader(f))


def process_rows(rows, do_commit=True, log_dir=None):
    """
    Process CSV rows. If do_commit is False, runs a dry-run and does not modify DB.
    Returns (stats_dict, log_text, log_path_or_None)
    """
    created_conn = 0
    updated_conn = 0
    created_app = 0
    lines = []

    def parse_date(s):
        if not s:
            return None
        s = s.strip()
        for fmt in ('%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d'):
            try:
                return datetime.strptime(s, fmt).date()
            except Exception:
                continue
        return None

    # Optionally run in a transaction
    if do_commit:
        atomic_ctx = transaction.atomic()
    else:
        # noop context manager
        from contextlib import nullcontext
        atomic_ctx = nullcontext()

    with atomic_ctx:
        for idx, row in enumerate(rows, start=1):
            id_number = row.get('ID_Number') or row.get('IDNumber') or row.get('ID')
            applicant_data = {
                'Applicant_Name': row.get('Applicant_Name') or '',
                'Gender': row.get('Gender') or '',
                'District': row.get('District') or '',
                'State': row.get('State') or '',
                'Pincode': int(float(row.get('Pincode') or 0)) if row.get('Pincode') else None,
                'Ownership': row.get('Ownership') or '',
                'GovtID_Type': row.get('GovtID_Type') or '',
                'IDNumber': id_number if id_number is not None else '',
                'Category': row.get('Category') or '',
            }

            # create/update applicant
            idnum = (applicant_data.get('IDNumber') or '').strip()
            if idnum:
                applicant, app_created = Applicant.objects.update_or_create(
                    IDNumber=idnum,
                    defaults=applicant_data
                )
                if app_created:
                    created_app += 1
                    lines.append(f'{idx}: Created applicant by ID {idnum}')
                else:
                    lines.append(f'{idx}: Updated applicant by ID {idnum}')
            else:
                try:
                    applicant = Applicant.objects.get(
                        Applicant_Name=applicant_data.get('Applicant_Name'),
                        District=applicant_data.get('District'),
                        Pincode=applicant_data.get('Pincode')
                    )
                    app_created = False
                    lines.append(f'{idx}: Matched existing applicant by name/district/pincode')
                except Applicant.DoesNotExist:
                    if do_commit:
                        applicant = Applicant.objects.create(**{k: v for k, v in applicant_data.items() if v is not None})
                    else:
                        applicant = None
                    app_created = True
                    created_app += 1
                    lines.append(f'{idx}: Created new applicant (no ID)')

            # status
            status_name = (row.get('Status') or '').strip()
            status_obj = None
            if status_name:
                if do_commit:
                    status_obj, _ = Status.objects.get_or_create(Status_Name=status_name)
                else:
                    status_obj = None

            conn_values = {
                'Applicant': applicant,
                'Load_Applied': int(float(row.get('Load_Applied') or 0)),
                'Date_of_Application': parse_date(row.get('Date_of_Application')),
                'Date_of_Approval': parse_date(row.get('Date_of_Approval')),
                'Modified_Date': parse_date(row.get('Modified_Date')),
                'Status': status_obj,
                'Reviewer_ID': int(float(row.get('Reviewer_ID') or 0)),
                'Reviewer_Name': row.get('Reviewer_Name') or '',
                'Reviewer_Comments': row.get('Reviewer_Comments') or '',
            }

            conn_id = row.get('ID')
            try:
                conn_id_int = int(float(conn_id)) if conn_id else None
            except Exception:
                conn_id_int = None

            if conn_id_int and Connection.objects.filter(id=conn_id_int).exists():
                if do_commit:
                    Connection.objects.filter(id=conn_id_int).update(**conn_values)
                updated_conn += 1
                lines.append(f'{idx}: Updated Connection id={conn_id_int}')
            else:
                if do_commit:
                    Connection.objects.create(**conn_values)
                created_conn += 1
                lines.append(f'{idx}: Created Connection')

    # write log if requested
    log_path = None
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        ts = timezone.now().strftime('%Y%m%d-%H%M%S')
        log_path = os.path.join(log_dir, f'import-{ts}.log')
        with open(log_path, 'w', encoding='utf-8') as lf:
            lf.write(f'Import run at {timezone.now().isoformat()}\n')
            lf.write('\n'.join(lines))

    stats = {
        'created_applicants': created_app,
        'created_connections': created_conn,
        'updated_connections': updated_conn,
        'total_rows': len(rows),
    }

    return stats, '\n'.join(lines), log_path
