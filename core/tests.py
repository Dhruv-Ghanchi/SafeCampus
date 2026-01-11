from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from .forms import IncidentReportForm, MessageForm
from django.utils import timezone


class UploadValidationTests(TestCase):
	def test_incident_evidence_too_large(self):
		# Create a fake large file
		large_content = b'a' * (settings.MAX_UPLOAD_SIZE + 1)
		f = SimpleUploadedFile('large.pdf', large_content, content_type='application/pdf')
		form = IncidentReportForm(data={
			'title': 'T', 'description': 'D', 'location': 'L', 'incident_date': timezone.now().strftime('%Y-%m-%dT%H:%M')
		}, files={'evidence': f})
		self.assertFalse(form.is_valid())
		self.assertIn('evidence', form.errors)

	def test_message_attachment_bad_type(self):
		bad = SimpleUploadedFile('malicious.exe', b'xyz', content_type='application/octet-stream')
		form = MessageForm(data={'text': 'hi'}, files={'attachment': bad})
		self.assertFalse(form.is_valid())
		self.assertIn('attachment', form.errors)

	def test_valid_image_attachment(self):
		img = SimpleUploadedFile('img.png', b'pngdata', content_type='image/png')
		form = MessageForm(data={'text': 'ok'}, files={'attachment': img})
		self.assertTrue(form.is_valid())

	def test_attachment_idempotency_same_file(self):
		# Create a user and incident, then post the same attachment twice
		from .models import User, Incident, Message
		user = User.objects.create_user(username='u1', password='pass', role='student')
		self.client.login(username='u1', password='pass')
		incident = Incident.objects.create(
			title='T', description='D', location='L', incident_date=timezone.now(), reporter=user, case_token='TST001'
		)
		# Create identical files (same name and content)
		f = SimpleUploadedFile('dup.png', b'imagebytes', content_type='image/png')
		resp1 = self.client.post(f'/my-case/{incident.id}/chat/', {'message': '', 'attachment': f})
		# Post again same file
		f2 = SimpleUploadedFile('dup.png', b'imagebytes', content_type='image/png')
		resp2 = self.client.post(f'/my-case/{incident.id}/chat/', {'message': '', 'attachment': f2})
		msgs = Message.objects.filter(incident=incident, sender=user)
		self.assertEqual(msgs.count(), 1)
