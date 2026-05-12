from django.core.management.base import BaseCommand, CommandError
import csv, io
from datetime import datetime

from app.models import Applicant, Connection, Status
from app.utils import read_csv_rows, process_rows


class Command(BaseCommand):
    help = 'Import connections and applicants from a CSV file (default: electricity_board_case_study.csv)'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help='Path to CSV file', default='electricity_board_case_study.csv')

    def handle(self, *args, **options):
        path = options['path']
        try:
            # try utf-8 first, then fall back to common Windows encoding
            # open with utf-8 first; if decoding fails while reading, fall back to cp1252
            f = open(path, newline='', encoding='utf-8')
            try:
                reader = csv.DictReader(f)
                rows = list(reader)
            except UnicodeDecodeError:
                f.close()
                f = open(path, newline='', encoding='cp1252')
                reader = csv.DictReader(f)
                rows = list(reader)

            created_conn = 0
            updated_conn = 0
            created_app = 0
            for row in rows:
                id_number = row.get('ID_Number') or row.get('IDNumber') or row.get('ID')
                applicant_data = {
                    'Applicant_Name': row.get('Applicant_Name') or '',
                    'Gender': row.get('Gender') or '',
                    'District': row.get('District') or '',
                    try:
                        rows = read_csv_rows(path)
                        stats, log_text, log_path = process_rows(rows, do_commit=True, log_dir=os.path.join('..', 'import_logs'))
                        # normalize log_path to project-relative
                        if log_path:
                            log_path = os.path.abspath(log_path)
                        self.stdout.write(self.style.SUCCESS(f"Import complete. Applicants created: {stats['created_applicants']}; Connections created: {stats['created_connections']}; Connections updated: {stats['updated_connections']}\nLog: {log_path}"))
                # If IDNumber is provided, use it as the unique key.
