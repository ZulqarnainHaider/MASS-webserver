#!/usr/bin/env python

from flask import render_template, redirect, request, Flask, url_for, abort, send_from_directory
from flask_wtf import FlaskForm, csrf
from wtforms import StringField, FieldList, FormField, SubmitField, IntegerField, FloatField, validators, BooleanField
import yaml, sys, binascii, os
from server_scripts import Parse, misc

# --------------------- CONFIGURATIONS -------------------------------------------------------------------------------------------------------
APP = Flask(__name__)
CSRF = csrf.CSRFProtect()
CSRF.init_app(APP)
APP.config['SECRET_KEY'] = os.urandom(32)
APP.config['UPLOAD_FOLDER'] = 'data'

with open("server_config.yaml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit()

# global variables for holding data (temporarily)
global nPop, nPlant, lifeSpan
global populations, plants, tech_form, techs, params 	# techs has class TechnologiesForm and has the input data
														# tech_form is the form to be rendered to web interface

@APP.route('/', methods = ['GET'])
def index():
	return(render_template('index.html'))
#----------- web page to ask for input size ---------------------------------------------------------------------------------------------------
class NRow(FlaskForm):
	NPop = IntegerField('Number of populations', validators = [validators.InputRequired(), validators.NumberRange(min=0)])
	NPlant = IntegerField('Number of plants', validators = [validators.InputRequired(), validators.NumberRange(min=0)])
	LifeSpan = IntegerField('Life Span of project', validators = [validators.InputRequired(), validators.NumberRange(min=0)])	

@APP.route('/input_size', methods=['GET', 'POST'])
def input_size():
	""" render webpage to ask for input sizes, save data to global nPop, nPlant, lifeSpan 
		then redirect to population_input """
	global nPop, nPlant, lifeSpan
	nRow = NRow()
	if request.method == 'GET':		
		return(render_template('input_size.html', nRow=nRow))
	if request.method == 'POST':
		if nRow.validate_on_submit():
			nPop = nRow.NPop.data
			nPlant = nRow.NPlant.data
			lifeSpan = nRow.LifeSpan.data
			APP.logger.info("transfer to {}".format(url_for('population_input')))
			return(redirect(url_for('population_input')))
		else:
			return(render_template('input_size.html', nRow=nRow))

#----------- webpage to ask for populations ------------------------------------------------------------------------------------------------------------
class OnePopulation(FlaskForm):
	Name = StringField('Cluster Name', validators = [validators.DataRequired()])
	Pr = IntegerField('Current Population', validators = [validators.DataRequired(), validators.NumberRange(min=0)])
	GrowthRate = FloatField('Population Growth Rate', validators = [validators.DataRequired()])
	lat = FloatField('Latitude', validators = [validators.DataRequired()])
	lon = FloatField('Longitude', validators = [validators.DataRequired()])
class PopulationsForm(FlaskForm):
	rows = FieldList(FormField(OnePopulation), min_entries = 0)

@APP.route('/population_input', methods=['GET', 'POST'])
def population_input():
	""" render webpage to ask for population input, save data to global populations (class PopulationsForm) 
		then redirect to plant_input """
	global nPop
	global populations

	if request.method == 'GET':
		APP.logger.info('creating a fresh populations form')
		populations = PopulationsForm()
		try: nPop
		except NameError:
			abort(400, 'Number of populations not found')
		else:
			for i in range(nPop):
				populations.rows.append_entry({'r': i+1})
		return(render_template('population_input.html', populations = populations))

	if request.method == 'POST':
		if request.form['command'] == 'Next':
			if populations.validate():
				APP.logger.info('transfer to {}'.format(url_for('plant_input')))
				return(redirect(url_for('plant_input')))
			else:
				return(render_template('population_input.html', populations = populations))
		elif request.form['command'] == 'Parse':
			populations = Parse.fill_populations(request.form['ExcelData'], populations)
			return(render_template('population_input.html', populations = populations))
		else:
			abort(400, 'Unknown request')

	# TODO: calculate projected population

# ------------- webpage to ask for plants --------------------------------------------------------------------------------------------------------------------
class OnePlant(FlaskForm):
	LocationName = StringField('Location Name')
	lat = FloatField('Latitude')
	lon = FloatField('Longitude')
class PlantsForm(FlaskForm):
	rows = FieldList(FormField(OnePlant), min_entries = 0)

@APP.route('/plant_input', methods = ['GET', 'POST'])
def plant_input():
	""" render webpage to ask for plants input, save data to global plants (class PlantsForm) 
		then redirect to tech_input """
	global nPlant
	global plants	
	
	if request.method == 'GET':
		APP.logger.info('creating a fresh plants form')
		plants = PlantsForm()
		try: nPlant
		except NameError:
			abort(400, 'Number of plants not found')
		else:
			for i in range(nPlant):
				plants.rows.append_entry({'k': i+1})
			return(render_template('plant_input.html', plants = plants))

	if request.method == 'POST':
		if request.form['command'] == 'Next':
			if plants.validate():
				APP.logger.info("transfer to {}".format(url_for('tech_input')))
				return(redirect(url_for('tech_input')))
			else:
				return(render_template('plant_input.html', plants = plants))
		elif request.form['command'] == 'Parse':
			plants = Parse.fill_plants(request.form['ExcelData'], plants)
			return(render_template('plant_input.html', plants = plants))
		else:
			abort(400, 'Unknown request')


# ------------- webpage to ask for techs ---------------------------------------------------------------------------------------------------------------------
class OneScale(FlaskForm): # defining technology numbers in each scale
	Capkt = FloatField('Capkt (m3/year)')
	CCkt = FloatField('CCkt ($/(m3/year))')
	OCt = FloatField('OCt ($/m3)')
	SRWt = FloatField('SRWt ($/m3)')
	GPt = FloatField('GPt (gr CO2-eq/m3)')
class OneTech(FlaskForm):
	Select = BooleanField('Check to select')
	Technology = StringField('Technology')
	Small = FormField(OneScale)
	Medium = FormField(OneScale)
	Large = FormField(OneScale)
class TechnologiesForm(FlaskForm):	
	rows = FieldList(FormField(OneTech), min_entries = 0)	
	
class CombinedForm(FlaskForm):
	""" This form is for convenient display on the web  """
	default_techs = FormField(TechnologiesForm)
	additional_techs = FormField(TechnologiesForm)
	n_additional = IntegerField('Add more techs')
	addMoreTechs = SubmitField('Input more Technologies')
	submit = SubmitField('Next')

@APP.route('/tech_input', methods = ['GET', 'POST'])
def tech_input():
	""" render webpage to ask for plants input, save data to global techs (class TechnologiesForm) 
		then redirect to parameter_input"""
	global config, techs
	default_techs = config['techs']
	tech_form = CombinedForm(n_additional = 0)
	if request.method == 'GET':
		# load default tech data from server_config.yaml file
		for t in default_techs:
			tech_form.default_techs.rows.append_entry({
				'Technology': t,
				'Small': default_techs[t]['Small'],
				'Medium': default_techs[t]['Medium'],
				'Large': default_techs[t]['Large']
			})
		return(render_template('tech_input.html', techs = tech_form))

	if request.method == 'POST':
		if tech_form.addMoreTechs.data:
			# reset additional tech data
			for r in range(tech_form.additional_techs.rows.__len__()):
				tech_form.additional_techs.rows.pop_entry()
			# add additional tech data
			for i in range(tech_form.n_additional.data):
				tech_form.additional_techs.rows.append_entry()
			return(render_template('tech_input.html', techs = tech_form))
		if tech_form.submit.data:
			techs = misc.tech_combine(tech_form)
			APP.logger.info("transfer to {}".format(url_for('parameter_input')))
			return(redirect(url_for('parameter_input')))		

# ------------- webpage to ask for parameters ---------------------------------------------------------------------------------------------------------
class OneParam(FlaskForm):
	Label = StringField('Parameter')
	Unit = StringField('Unit')
	Value = FloatField('Value')
class ParamsForm(FlaskForm):
	rows = FieldList(FormField(OneParam), min_entries = 0)
	submit = SubmitField('Next')

@APP.route('/parameter_input', methods = ['POST', 'GET'])
def parameter_input():
	""" render webpage to ask for parameter input, save data to global params (class ParamsForm) """
	global params
	default_params = config['params']
	params = ParamsForm()
	if request.method == 'GET':
		for p in default_params:
			params.rows.append_entry(p)			
		return(render_template('param_input.html', params = params))

	if request.method == 'POST':
		APP.logger.info("transfer to {}".format(url_for('review')))
		return(redirect(url_for('review')))


# ------------ review input data ----------------------------------------------------------------------------------------------------------------------------------
@APP.route('/review', methods = ['POST', 'GET'])
def review():
	""" review input data before running optimizer
		TODO: create links for editing data """
	global nPop, nPlant, lifeSpan, populations, plants, techs, params

	if request.method == 'GET':
		return(render_template('review.html', nPop = nPop, nPlant = nPlant, lifeSpan = lifeSpan,
			populations = populations, plants = plants, techs = techs, params = params))

# ------------ run optimizer -------------------------------------------------------------------------------------------------------------------------------------------
@APP.route('/run_optimizer', methods = ['POST'])
def run_optimizer():
	global nPop, nPlant, lifeSpan, populations, plants, techs, params
	if request.form['command'] == 'Run optimizer':
		misc.write_excel(populations, plants, techs, params, APP.config['UPLOAD_FOLDER'], filename = 'Data.xls')
		return(send_from_directory(APP.config['UPLOAD_FOLDER'], 'Data.xls', as_attachment=True))
	else:
		abort(400, 'Unknown command')


# --------------------- RUN SERVER ---------------------------------------------------------------------------------------------------------------------------------------#
if __name__ == '__main__':
    APP.debug=True
    APP.run(host = "0.0.0.0", port = 10000, threaded=True)