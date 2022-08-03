from odoo import models, fields, api,_
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

class BankPassbook(models.Model):
	_name = 'bank.passbook'
	_description = 'Bank Passbook'
	_rec_name = 'customer_name'

	state = fields.Selection([('new','New'),('update','Updated'),('done','Done')],string="State", default="new")
	name = fields.Char('Name',default="Bank Of India",readonly=True)
	names = fields.Char('Names',default="बैंक ऑफ इंडिया",readonly=True)
	date = fields.Date('Date', default=datetime.today())
	ac_type = fields.Selection([('saving','Saving A/c'),('current','Current A/c')],string="Account Type")
	cifi_no = fields.Char('CIF No.')
	account_no = fields.Char('Account No.')
	customer_name = fields.Char('Customer Name')
	street = fields.Char()
	street2 = fields.Char()
	city = fields.Char()
	state_id = fields.Char()
	zip = fields.Char()
	country_id = fields.Char()
	phone = fields.Char('Phone No.')
	email = fields.Char('Email Id')
	dob = fields.Char('Date Of Birth')
	marital_status = fields.Selection([('married','Married'),('unmarried','Un-Married')],string="Marital Status")
	total_credit = fields.Float('Total Credit')
	credit_balance = fields.Float('Credit Balance')
	total_dabit = fields.Float('Total Dabit')
	dabit_balance = fields.Float('Dabit Balance')
	total_balance = fields.Float('Total Balance',compute="compute_total_credit")
	bank_entry_line = fields.One2many('bank.entry.line','bank_entry_id')
	loan_assumtion_line = fields.One2many('loan.assumtion.line','assumtion_id')
	loan_amt = fields.Float('Loan Amount')
	interest = fields.Float('Interest')
	payment_start_date = fields.Date('Payment Start Date', default=datetime.today())
	installment_no = fields.Integer('Installment Number')
	unpaid_amount = fields.Float('UnPaid Amount', related="total_amt", readonly=False)
	paid_amount = fields.Float('Paid Amount')
	loan_status = fields.Selection([('loan_paid','Loan Paid'),('loan_pending','Loan Pending')])
	total_amt = fields.Float('Total Amt With Interest')
	year = fields.Float('Year')

	def action_new(self):
		self.state = 'new'
		
	def action_loan_count(self):
		if self.loan_amt == 0.00 or self.interest == 0.00 or self.year == 0 :
			raise UserError(_("Loan Amt is 0.00 !! Plz Enter Valid Amount !!"))
		else:
			self.installment_no = self.year * 12
			installment_num =  self.installment_no
			date = self.payment_start_date
			total_interest = self.loan_amt * self.interest / 100
			self.total_amt = self.loan_amt + total_interest
			emi_amt = (self.loan_amt + total_interest) / installment_num

			for line in range(installment_num):
				val = {
				"payment_date":date,
				"amount":emi_amt,
				"status":'pending'
				}
				self.loan_assumtion_line = [(0,0,val)]
				date = date + relativedelta(months=1)

	def action_all_clear(self):
		self.loan_amt = 0.00
		self.interest = 0.00
		self.installment_no = 0
		self.unpaid_amount = 0.00
		self.paid_amount = 0.00
		self.loan_status = ''
		for line in self.loan_assumtion_line:
			self.loan_assumtion_line = [(2,line.id)]

	def action_update(self):
		self.state = 'update'

	def action_done(self):
		self.state = 'done'

	@api.depends('bank_entry_line')
	def compute_total_credit(self):
		for rec in self:
			rec.total_balance = 0
			for line in rec.bank_entry_line:
				if line.select_type == 'credit':
					rec.total_balance += line.credit
				else:
					rec.total_balance -= line.dabit

class BankEntryLine(models.Model):
	_name = 'bank.entry.line'
	_description = 'Bank Entry Line'

	bank_entry_id = fields.Many2one('bank.passbook')
	date = fields.Date('Date', default=datetime.today())
	description = fields.Text('Credit / Dabit description')
	select_type = fields.Selection([('credit','Credit'),('dabit','Dabit')],string="Select Type")
	credit = fields.Float('Credit')
	dabit = fields.Float('Dabit')

class LoanAssumtionLine(models.Model):
	_name = 'loan.assumtion.line'
	_description = 'Loan Assumtion Line'

	assumtion_id = fields.Many2one('bank.passbook','Loan Assumtion Id')
	payment_date = fields.Date('Payment Date')
	amount = fields.Float('Amount')
	status = fields.Selection([('pending','Pending'),('paid','Paid')])

	def action_to_done(self):
		self.status = 'paid'
		self.assumtion_id.unpaid_amount -= self.amount
		self.assumtion_id.paid_amount += self.amount
		
		if self.assumtion_id.total_amt == self.assumtion_id.paid_amount:
			self.assumtion_id.loan_status = 'loan_paid'
		else:
			self.assumtion_id.loan_status = 'loan_pending'

