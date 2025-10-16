"""
Management command to seed file-related tools into the database.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from llm_tools.models import ToolDefinition
import os


class Command(BaseCommand):
    help = 'Seed file-related tools into the database'

    def handle(self, *args, **options):
        self.stdout.write('Seeding file-related tools...')
        
        # Get the base path for scripts
        base_path = os.path.join(settings.BASE_DIR, 'tools', 'scripts')
        
        # Create scan_receipt tool
        self.create_scan_receipt_tool(base_path)
        
        # Create download_music tool
        self.create_download_music_tool(base_path)
        
        # Create generate_pdf_report tool
        self.create_generate_pdf_report_tool(base_path)
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded file tools!'))
    
    def create_scan_receipt_tool(self, base_path):
        """Create the scan_receipt tool"""
        script_path = os.path.join(base_path, 'scan_receipt.py')
        
        tool, created = ToolDefinition.objects.get_or_create(
            name='scan_receipt',
            defaults={
                'display_name': 'Scan Receipt',
                'category': 'information',
                'description': '''Scan a receipt image and extract information using OCR.

Use this tool when the user:
- Uploads a receipt image and wants to extract data
- Asks to scan or read a receipt
- Wants to know what's on a receipt

This tool extracts:
- Merchant name
- Date
- Total amount
- Items and prices
- Category

The file must already be uploaded via /api/files/upload.

Examples:
- "Scan this receipt for me"
- "What's the total on this receipt?"
- "Extract the items from my receipt"''',
                'usage_examples': [
                    'User uploads receipt and asks to scan it',
                    'User wants to extract receipt information',
                    'User asks about receipt details'
                ],
                'execution_type': 'script',
                'script_path': script_path,
                'script_timeout': 60,
                'parameters_schema': {
                    'type': 'object',
                    'properties': {
                        'file_id': {
                            'type': 'string',
                            'description': 'ID of the uploaded receipt image file'
                        }
                    },
                    'required': ['file_id']
                },
                'response_schema': {
                    'type': 'object',
                    'properties': {
                        'success': {'type': 'boolean'},
                        'file_id': {'type': 'string'},
                        'receipt_data': {
                            'type': 'object',
                            'properties': {
                                'merchant': {'type': 'string'},
                                'date': {'type': 'string'},
                                'total': {'type': 'number'},
                                'items': {'type': 'array'}
                            }
                        }
                    }
                },
                'is_active': True,
                'requires_auth': True,
                'version': '1.0'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'  Created tool: {tool.name}'))
        else:
            self.stdout.write(f'  Tool already exists: {tool.name}')
    
    def create_download_music_tool(self, base_path):
        """Create the download_music tool"""
        script_path = os.path.join(base_path, 'download_music.py')
        
        tool, created = ToolDefinition.objects.get_or_create(
            name='download_music',
            defaults={
                'display_name': 'Download Music',
                'category': 'information',
                'description': '''Download audio from YouTube or other sources.

Use this tool when the user:
- Wants to download music or audio
- Provides a YouTube URL or other audio source
- Asks to save a song

This tool:
- Downloads audio using yt-dlp
- Converts to MP3 format
- Saves to user's file storage
- Returns download link

Examples:
- "Download this song: [URL]"
- "Save this music for me"
- "Get the audio from this video"''',
                'usage_examples': [
                    'User provides YouTube URL to download',
                    'User wants to save music',
                    'User asks to download audio'
                ],
                'execution_type': 'script',
                'script_path': script_path,
                'script_timeout': 120,
                'parameters_schema': {
                    'type': 'object',
                    'properties': {
                        'url': {
                            'type': 'string',
                            'description': 'URL to download audio from (YouTube, etc.)'
                        }
                    },
                    'required': ['url']
                },
                'response_schema': {
                    'type': 'object',
                    'properties': {
                        'success': {'type': 'boolean'},
                        'file_id': {'type': 'string'},
                        'filename': {'type': 'string'},
                        'download_url': {'type': 'string'}
                    }
                },
                'is_active': True,
                'requires_auth': True,
                'version': '1.0'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'  Created tool: {tool.name}'))
        else:
            self.stdout.write(f'  Tool already exists: {tool.name}')
    
    def create_generate_pdf_report_tool(self, base_path):
        """Create the generate_pdf_report tool"""
        script_path = os.path.join(base_path, 'generate_pdf_report.py')
        
        tool, created = ToolDefinition.objects.get_or_create(
            name='generate_pdf_report',
            defaults={
                'display_name': 'Generate PDF Report',
                'category': 'information',
                'description': '''Generate PDF reports from user data.

Use this tool when the user:
- Wants a downloadable report
- Asks for a summary of their wellbeing, tasks, or activities
- Requests a PDF export of their data

Report types:
- **wellbeing**: Check-ins, emotions, daily logs
- **tasks**: Task completion and productivity
- **summary**: Overall summary

Examples:
- "Generate a wellbeing report for the last month"
- "Create a PDF of my check-ins"
- "I want a summary report"''',
                'usage_examples': [
                    'User wants wellbeing report',
                    'User requests PDF export',
                    'User asks for summary document'
                ],
                'execution_type': 'script',
                'script_path': script_path,
                'script_timeout': 90,
                'parameters_schema': {
                    'type': 'object',
                    'properties': {
                        'report_type': {
                            'type': 'string',
                            'enum': ['wellbeing', 'tasks', 'summary'],
                            'description': 'Type of report to generate'
                        },
                        'days': {
                            'type': 'integer',
                            'description': 'Number of days to include in report (default: 30)'
                        }
                    },
                    'required': ['report_type']
                },
                'response_schema': {
                    'type': 'object',
                    'properties': {
                        'success': {'type': 'boolean'},
                        'file_id': {'type': 'string'},
                        'filename': {'type': 'string'},
                        'download_url': {'type': 'string'}
                    }
                },
                'is_active': True,
                'requires_auth': True,
                'version': '1.0'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'  Created tool: {tool.name}'))
        else:
            self.stdout.write(f'  Tool already exists: {tool.name}')
