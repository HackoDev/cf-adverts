from django import template
# from donations.models import Payment


register = template.Library()


@register.filter()
def load_project_from_payment(invoice_id):
    # TODO: вынести template tag в приложение payments Payment
    if invoice_id and invoice_id.isdigit():
        try:
            payment = Payment.objects.get(pk=invoice_id)
        except Payment.DoesNotExist:
            pass
        else:
            return payment.project
