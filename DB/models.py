from peewee import MySQLDatabase, AutoField, CharField, DecimalField, TextField, IntegerField, SQL, Model, \
    ForeignKeyField, DateTimeField
from HLM_PV_Import.settings import HEDB
from playhouse.shortcuts import ReconnectMixin


# noinspection PyAbstractClass
class ReconnectMySQLDatabase(ReconnectMixin, MySQLDatabase):
    pass


database = ReconnectMySQLDatabase(HEDB.NAME, user=HEDB.USER, password=HEDB.PASS, host=HEDB.HOST, port=3306,
                                  autoconnect=False)


class UnknownField(object):
    def __init__(self, *_, **__): pass


class BaseModel(Model):
    class Meta:
        database = database


class GamNetwork(BaseModel):
    nw_comment = CharField(column_name='NW_COMMENT', null=True)
    nw_id = AutoField(column_name='NW_ID')
    nw_name = CharField(column_name='NW_NAME')
    nw_outofoperation = DecimalField(column_name='NW_OUTOFOPERATION', constraints=[SQL("DEFAULT 0")])

    class Meta:
        table_name = 'gam_network'


class GamImage(BaseModel):
    img_blob = TextField(column_name='IMG_BLOB', null=True)
    img_comment = CharField(column_name='IMG_COMMENT')
    img_diameter = IntegerField(column_name='IMG_DIAMETER', null=True)
    img_id = AutoField(column_name='IMG_ID')
    img_name = CharField(column_name='IMG_NAME')
    img_nw = ForeignKeyField(column_name='IMG_NW_ID', field='nw_id', model=GamNetwork)
    img_outofoperation = DecimalField(column_name='IMG_OUTOFOPERATION', constraints=[SQL("DEFAULT 0")])

    class Meta:
        table_name = 'gam_image'


class GamDisplayformat(BaseModel):
    df_alarmhigh = DecimalField(column_name='DF_ALARMHIGH', null=True)
    df_alarmlow = DecimalField(column_name='DF_ALARMLOW', null=True)
    df_decimalplaces = DecimalField(column_name='DF_DECIMALPLACES', null=True)
    df_id = AutoField(column_name='DF_ID')
    df_lowerlimit = DecimalField(column_name='DF_LOWERLIMIT', null=True)
    df_ratetype = DecimalField(column_name='DF_RATETYPE', null=True)
    df_upperlimit = DecimalField(column_name='DF_UPPERLIMIT', null=True)

    class Meta:
        table_name = 'gam_displayformat'


class GamDisplaygroup(BaseModel):
    dg_id = AutoField(column_name='DG_ID')
    dg_name = CharField(column_name='DG_NAME', null=True)
    dg_outofoperation = DecimalField(column_name='DG_OUTOFOPERATION', constraints=[SQL("DEFAULT 0")])

    class Meta:
        table_name = 'gam_displaygroup'


class GamFunction(BaseModel):
    of_comment = CharField(column_name='OF_COMMENT', null=True)
    of_id = AutoField(column_name='OF_ID')
    of_name = CharField(column_name='OF_NAME', null=True)

    class Meta:
        table_name = 'gam_function'


class GamObjectclass(BaseModel):
    oc_comment = CharField(column_name='OC_COMMENT', null=True)
    oc_df_id_1 = ForeignKeyField(column_name='OC_DF_ID_1', field='df_id', model=GamDisplayformat, null=True)
    oc_df_id_2 = ForeignKeyField(backref='gam_displayformat_oc_df_id_2_set', column_name='OC_DF_ID_2', field='df_id',
                                 model=GamDisplayformat, null=True)
    oc_df_id_3 = ForeignKeyField(backref='gam_displayformat_oc_df_id_3_set', column_name='OC_DF_ID_3', field='df_id',
                                 model=GamDisplayformat, null=True)
    oc_df_id_4 = ForeignKeyField(backref='gam_displayformat_oc_df_id_4_set', column_name='OC_DF_ID_4', field='df_id',
                                 model=GamDisplayformat, null=True)
    oc_df_id_5 = ForeignKeyField(backref='gam_displayformat_oc_df_id_5_set', column_name='OC_DF_ID_5', field='df_id',
                                 model=GamDisplayformat, null=True)
    oc_displaypriority = DecimalField(column_name='OC_DISPLAYPRIORITY', null=True)
    oc_function = ForeignKeyField(column_name='OC_FUNCTION_ID', field='of_id', model=GamFunction)
    oc_icon0 = CharField(column_name='OC_ICON0', null=True)
    oc_icon20 = CharField(column_name='OC_ICON20', null=True)
    oc_icon40 = CharField(column_name='OC_ICON40', null=True)
    oc_icon60 = CharField(column_name='OC_ICON60', null=True)
    oc_icon80 = CharField(column_name='OC_ICON80', null=True)
    oc_icon_alarm = CharField(column_name='OC_ICON_ALARM', null=True)
    oc_id = AutoField(column_name='OC_ID')
    oc_measuretype1 = CharField(column_name='OC_MEASURETYPE1', null=True)
    oc_measuretype2 = CharField(column_name='OC_MEASURETYPE2', null=True)
    oc_measuretype3 = CharField(column_name='OC_MEASURETYPE3', null=True)
    oc_measuretype4 = CharField(column_name='OC_MEASURETYPE4', null=True)
    oc_measuretype5 = CharField(column_name='OC_MEASURETYPE5', null=True)
    oc_name = CharField(column_name='OC_NAME')
    oc_positiontype = DecimalField(column_name='OC_POSITIONTYPE')

    class Meta:
        table_name = 'gam_objectclass'


class GamObjecttype(BaseModel):
    ot_calib_name = CharField(column_name='OT_CALIB_NAME', null=True)
    ot_calib_npoints = IntegerField(column_name='OT_CALIB_NPOINTS', null=True)
    ot_calib_x = CharField(column_name='OT_CALIB_X', null=True)
    ot_calib_y = CharField(column_name='OT_CALIB_Y', null=True)
    ot_comment = CharField(column_name='OT_COMMENT', null=True)
    ot_df_id_1 = ForeignKeyField(column_name='OT_DF_ID_1', field='df_id', model=GamDisplayformat, null=True)
    ot_df_id_2 = ForeignKeyField(backref='gam_displayformat_ot_df_id_2_set', column_name='OT_DF_ID_2', field='df_id',
                                 model=GamDisplayformat, null=True)
    ot_df_id_3 = ForeignKeyField(backref='gam_displayformat_ot_df_id_3_set', column_name='OT_DF_ID_3', field='df_id',
                                 model=GamDisplayformat, null=True)
    ot_df_id_4 = ForeignKeyField(backref='gam_displayformat_ot_df_id_4_set', column_name='OT_DF_ID_4', field='df_id',
                                 model=GamDisplayformat, null=True)
    ot_df_id_5 = ForeignKeyField(backref='gam_displayformat_ot_df_id_5_set', column_name='OT_DF_ID_5', field='df_id',
                                 model=GamDisplayformat, null=True)
    ot_id = AutoField(column_name='OT_ID')
    ot_internal_pcomp = DecimalField(column_name='OT_INTERNAL_PCOMP', null=True)
    ot_internal_tcomp = DecimalField(column_name='OT_INTERNAL_TCOMP', null=True)
    ot_model = CharField(column_name='OT_MODEL', null=True)
    ot_name = CharField(column_name='OT_NAME')
    ot_objectclass = ForeignKeyField(column_name='OT_OBJECTCLASS_ID', field='oc_id', model=GamObjectclass)
    ot_outofoperation = DecimalField(column_name='OT_OUTOFOPERATION', constraints=[SQL("DEFAULT 0")])
    ot_press_norm = DecimalField(column_name='OT_PRESS_NORM', null=True)
    ot_producer = CharField(column_name='OT_PRODUCER', null=True)
    ot_step = DecimalField(column_name='OT_STEP', null=True)
    ot_substance = CharField(column_name='OT_SUBSTANCE', null=True)
    ot_temp_norm = DecimalField(column_name='OT_TEMP_NORM', null=True)
    ot_volume = DecimalField(column_name='OT_VOLUME', null=True)

    class Meta:
        table_name = 'gam_objecttype'


class GamObject(BaseModel):
    ob_active = DecimalField(column_name='OB_ACTIVE', null=True)
    ob_adcloop = IntegerField(column_name='OB_ADCLOOP', null=True)
    ob_address = CharField(column_name='OB_ADDRESS', null=True)
    ob_aliasname = CharField(column_name='OB_ALIASNAME', null=True)
    ob_cellcount = DecimalField(column_name='OB_CELLCOUNT', null=True)
    ob_comment = CharField(column_name='OB_COMMENT', null=True)
    ob_comport = CharField(column_name='OB_COMPORT', null=True)
    ob_critvalue = DecimalField(column_name='OB_CRITVALUE', null=True)
    ob_df_id_1 = ForeignKeyField(column_name='OB_DF_ID_1', field='df_id', model=GamDisplayformat, null=True)
    ob_df_id_2 = ForeignKeyField(backref='gam_displayformat_ob_df_id_2_set', column_name='OB_DF_ID_2', field='df_id',
                                 model=GamDisplayformat, null=True)
    ob_df_id_3 = ForeignKeyField(backref='gam_displayformat_ob_df_id_3_set', column_name='OB_DF_ID_3', field='df_id',
                                 model=GamDisplayformat, null=True)
    ob_df_id_4 = ForeignKeyField(backref='gam_displayformat_ob_df_id_4_set', column_name='OB_DF_ID_4', field='df_id',
                                 model=GamDisplayformat, null=True)
    ob_df_id_5 = ForeignKeyField(backref='gam_displayformat_ob_df_id_5_set', column_name='OB_DF_ID_5', field='df_id',
                                 model=GamDisplayformat, null=True)
    ob_displaygroup = ForeignKeyField(column_name='OB_DISPLAYGROUP_ID', field='dg_id', model=GamDisplaygroup, null=True)
    ob_enabled1 = DecimalField(column_name='OB_ENABLED1', null=True)
    ob_enabled2 = DecimalField(column_name='OB_ENABLED2', null=True)
    ob_enabled3 = DecimalField(column_name='OB_ENABLED3', null=True)
    ob_endofoperation = DateTimeField(column_name='OB_ENDOFOPERATION', null=True)
    ob_filltimeout = IntegerField(column_name='OB_FILLTIMEOUT', null=True)
    ob_id = AutoField(column_name='OB_ID')
    ob_installed = DateTimeField(column_name='OB_INSTALLED', null=True)
    ob_ip = CharField(column_name='OB_IP', null=True)
    ob_lasttimeactive = DateTimeField(column_name='OB_LASTTIMEACTIVE', null=True)
    ob_longinterval = IntegerField(column_name='OB_LONGINTERVAL', null=True)
    ob_maxvalue = DecimalField(column_name='OB_MAXVALUE', null=True)
    ob_meascurrent = IntegerField(column_name='OB_MEASCURRENT', null=True)
    ob_minvalue = DecimalField(column_name='OB_MINVALUE', null=True)
    ob_name = CharField(column_name='OB_NAME')
    ob_nw = ForeignKeyField(column_name='OB_NW_ID', field='nw_id', model=GamNetwork, null=True)
    ob_objecttype = ForeignKeyField(column_name='OB_OBJECTTYPE_ID', field='ot_id', model=GamObjecttype)
    ob_offset_corrvolume = DecimalField(column_name='OB_OFFSET_CORRVOLUME', null=True)
    ob_offset_value = DecimalField(column_name='OB_OFFSET_VALUE', null=True)
    ob_offset_volume = DecimalField(column_name='OB_OFFSET_VOLUME', null=True)
    ob_posinformation = CharField(column_name='OB_POSINFORMATION', null=True)
    ob_quenchcurrent = IntegerField(column_name='OB_QUENCHCURRENT', null=True)
    ob_quenchtime = IntegerField(column_name='OB_QUENCHTIME', null=True)
    ob_send_delta_p = DecimalField(column_name='OB_SEND_DELTA_P', null=True)
    ob_send_delta_v = DecimalField(column_name='OB_SEND_DELTA_V', null=True)
    ob_serno = CharField(column_name='OB_SERNO', null=True)
    ob_shortinterval = IntegerField(column_name='OB_SHORTINTERVAL', null=True)
    ob_span1 = DecimalField(column_name='OB_SPAN1', null=True)
    ob_span2 = DecimalField(column_name='OB_SPAN2', null=True)
    ob_span3 = DecimalField(column_name='OB_SPAN3', null=True)
    ob_status = DecimalField(column_name='OB_STATUS', null=True)
    ob_substance1 = CharField(column_name='OB_SUBSTANCE1', null=True)
    ob_substance2 = CharField(column_name='OB_SUBSTANCE2', null=True)
    ob_substance3 = CharField(column_name='OB_SUBSTANCE3', null=True)
    ob_tare = DecimalField(column_name='OB_TARE', null=True)
    ob_value = DecimalField(column_name='OB_VALUE', null=True)
    ob_volume = DecimalField(column_name='OB_VOLUME', null=True)
    ob_waittime = IntegerField(column_name='OB_WAITTIME', null=True)
    ob_zero1 = DecimalField(column_name='OB_ZERO1', null=True)
    ob_zero2 = DecimalField(column_name='OB_ZERO2', null=True)
    ob_zero3 = DecimalField(column_name='OB_ZERO3', null=True)

    class Meta:
        table_name = 'gam_object'


class GamCoordinate(BaseModel):
    coo_id = AutoField(column_name='COO_ID')
    coo_img = ForeignKeyField(column_name='COO_IMG_ID', field='img_id', model=GamImage)
    coo_ob = ForeignKeyField(column_name='COO_OB_ID', field='ob_id', model=GamObject)
    coo_x = DecimalField(column_name='COO_X', null=True)
    coo_y = DecimalField(column_name='COO_Y', null=True)

    class Meta:
        table_name = 'gam_coordinate'


class GamMeasurement(BaseModel):
    mea_bookingcode = DecimalField(column_name='MEA_BOOKINGCODE', null=True)
    mea_comment = CharField(column_name='MEA_COMMENT', null=True)
    mea_date = DateTimeField(column_name='MEA_DATE')
    mea_date2 = DateTimeField(column_name='MEA_DATE2', null=True)
    mea_id = AutoField(column_name='MEA_ID')
    mea_object = ForeignKeyField(column_name='MEA_OBJECT_ID', field='ob_id', model=GamObject)
    mea_status = DecimalField(column_name='MEA_STATUS', null=True)
    mea_valid = DecimalField(column_name='MEA_VALID', null=True)
    mea_value1 = DecimalField(column_name='MEA_VALUE1', null=True)
    mea_value2 = DecimalField(column_name='MEA_VALUE2', null=True)
    mea_value3 = DecimalField(column_name='MEA_VALUE3', null=True)
    mea_value4 = DecimalField(column_name='MEA_VALUE4', null=True)
    mea_value5 = DecimalField(column_name='MEA_VALUE5', null=True)

    class Meta:
        table_name = 'gam_measurement'


class GamObjectrelation(BaseModel):
    or_bookingrequest = DecimalField(column_name='OR_BOOKINGREQUEST', null=True)
    or_date_assignment = DateTimeField(column_name='OR_DATE_ASSIGNMENT')
    or_date_removal = DateTimeField(column_name='OR_DATE_REMOVAL', null=True)
    or_id = AutoField(column_name='OR_ID')
    or_object = ForeignKeyField(column_name='OR_OBJECT_ID', field='ob_id', model=GamObject)
    or_object_id_assigned = ForeignKeyField(backref='gam_object_or_object_id_assigned_set',
                                            column_name='OR_OBJECT_ID_ASSIGNED', field='ob_id', model=GamObject)
    or_outflow = DecimalField(column_name='OR_OUTFLOW', null=True)
    or_primary = DecimalField(column_name='OR_PRIMARY', null=True)

    class Meta:
        table_name = 'gam_objectrelation'
