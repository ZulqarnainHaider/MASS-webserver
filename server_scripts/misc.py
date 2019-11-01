from math import sin, cos, acos, radians
from xlwt import Workbook
from flask_wtf import FlaskForm, csrf
from wtforms import StringField, FieldList, FormField, SubmitField, IntegerField, FloatField, validators, BooleanField
import os
	
""" HELPER FUNCTIONS """

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

def tech_combine(_techs):
	""" Combine selected techs.default_techs and techs.additional_techs
		return a TechnologiesForm object with selected techs
	"""
	selected_techs = TechnologiesForm()
	for t in  _techs.default_techs.rows:
		if t.Select.data: # if default tech is selected by user, add to selected_techs
			selected_techs.rows.append_entry(t)
	if _techs.additional_techs.rows.__len__() > 0:
		for t in _techs.additional_techs.rows:
			selected_techs.rows.append_entry(t)
	return(selected_techs)

def distance(lat1, lon1, lat2, lon2):
	""" distance (in miles) between 2 points on earth """
	return(0.000189394*
		(3963*acos(cos(radians(90-lat1))*cos(radians(90-lat2))+
			sin(radians(90-lat1))*sin(radians(90-lat2))*cos(radians(lon1-lon2))))*5280
	)
def distance_pop_plant(pops, plants):
	""" distance between populations and plants 
		pops has class PopulationsForm, plants has class PlantsForm
		returns a 2D array of size nPops*nPlants
	"""
	nPop = pops.rows.__len__()
	nPlant = plants.rows.__len__()
	# initialize output 
	out = [[0 for j in range(nPlant)] for i in range(nPop)]
	# loop through pops and plants
	for i in range(nPop):
		for j in range(nPlant):
			try:
				lat1 = float(pops.rows[i].lat.data)
				lon1 = float(pops.rows[i].lon.data)
				lat2 = float(plants.rows[j].lat.data)
				lon2 = float(plants.rows[j].lon.data)
			except ValueError:
				raise TypeError('cannot convert coordinates to float')
			out[i][j] = distance(lat1, lon1, lat2, lon2)
	return(out)

def write_excel(populations, plants, techs, params, directory, filename):
	""" write an excel file from given inputs """
	wb = Workbook()
	sheet1 = wb.add_sheet('Sheet 1')

	# write Populations to columns 0 to 4
	sheet1.write(0, 0, 'r'); sheet1.write(0, 1, 'Pr'); sheet1.write(0, 2, 'Population Growth Rate')
	sheet1.write(0, 3, 'Latitude'); sheet1.write(0, 4, 'Longitude')
	for r in range(populations.rows.__len__()):
		sheet1.write(r+1, 0, r + 1)
		sheet1.write(r+1, 1, populations.rows[r].Pr.data)
		sheet1.write(r+1, 2, populations.rows[r].GrowthRate.data)
		sheet1.write(r+1, 3, populations.rows[r].lat.data)
		sheet1.write(r+1, 4, populations.rows[r].lon.data)

	# write plants to columns 5 to 8
	sheet1.write(0, 5, 'k'); sheet1.write(0, 6, 'Location'); sheet1.write(0, 7, 'Latitude'); sheet1.write(0, 8, 'Longitude')
	for r in range(plants.rows.__len__()):
		sheet1.write(r+1, 5, r + 1)
		sheet1.write(r+1, 6, plants.rows[r].LocationName.data)
		sheet1.write(r+1, 7, plants.rows[r].lat.data)
		sheet1.write(r+1, 8, plants.rows[r].lon.data)

	# write technology to columns 9 to 16
	sheet1.write(0, 9, 'Technology'); sheet1.write(0, 10, 'Scale'); sheet1.write(0, 11, 't'); sheet1.write(0, 12, 'Capkt');
	sheet1.write(0, 13, 'CCkt'); sheet1.write(0, 14, 'OCt'); sheet1.write(0, 15, 'SRWt'); sheet1.write(0, 16, 'GPt')
	t = 0
	for techid in range(techs.rows.__len__()):
		r = 3*techid		
		sheet1.write_merge(r+1, r+3, 9, 9, techs.rows[techid].Technology.data.data)
		t+=1
		sheet1.write(r+1, 10, 'Small')
		sheet1.write(r+1, 11, t)
		sheet1.write(r+1, 12, techs.rows[techid].Small.Capkt.data.data)
		sheet1.write(r+1, 13, techs.rows[techid].Small.CCkt.data.data)
		sheet1.write(r+1, 14, techs.rows[techid].Small.OCt.data.data)
		sheet1.write(r+1, 15, techs.rows[techid].Small.SRWt.data.data)
		sheet1.write(r+1, 16, techs.rows[techid].Small.GPt.data.data)
		t+=1
		sheet1.write(r+2, 10, 'Medium')
		sheet1.write(r+2, 11, t)
		sheet1.write(r+2, 12, techs.rows[techid].Medium.Capkt.data.data)
		sheet1.write(r+2, 13, techs.rows[techid].Medium.CCkt.data.data)
		sheet1.write(r+2, 14, techs.rows[techid].Medium.OCt.data.data)
		sheet1.write(r+2, 15, techs.rows[techid].Medium.SRWt.data.data)
		sheet1.write(r+2, 16, techs.rows[techid].Medium.GPt.data.data)
		t+=1
		sheet1.write(r+3, 10, 'Large')
		sheet1.write(r+3, 11, t)
		sheet1.write(r+3, 12, techs.rows[techid].Large.Capkt.data.data)
		sheet1.write(r+3, 13, techs.rows[techid].Large.CCkt.data.data)
		sheet1.write(r+3, 14, techs.rows[techid].Large.OCt.data.data)
		sheet1.write(r+3, 15, techs.rows[techid].Large.SRWt.data.data)
		sheet1.write(r+3, 16, techs.rows[techid].Large.GPt.data.data)

	# write parameters to columns 17 to 19
	sheet1.write(0, 17, 'Parameter'); sheet1.write(0, 18, 'Unit'); sheet1.write(0, 19, 'Value')
	for r in range(params.rows.__len__()):
		sheet1.write(r+1, 17, params.rows[r].Label.data)
		sheet1.write(r+1, 18, params.rows[r].Unit.data)
		sheet1.write(r+1, 19, params.rows[r].Value.data)

	# write distance to columns 20 and above
	distance_matrix = distance_pop_plant(populations, plants)
	offset = 20
		# write headers
	for i in range(populations.rows.__len__()):
		sheet1.write(i+1, offset, 'r = ' + str(i+1))
	for j in range(plants.rows.__len__()):
		sheet1.write(0, offset+1+j, 'k = ' + str(j+1))
		# write data
	for i in range(populations.rows.__len__()):
		for j in range(plants.rows.__len__()):
			sheet1.write(i+1, offset+1+j, distance_matrix[i][j])

	# save to disk
	if not os.path.exists(directory):
		os.makedirs(directory)
	wb.save(directory+'/'+filename)