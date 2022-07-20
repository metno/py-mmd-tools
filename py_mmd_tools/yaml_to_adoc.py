import yaml
import jinja2
import pandas as pd

from pkg_resources import resource_string


def get_attr_info(key, convention, normalized):
    """Get information about the MMD fields.

    Input
    =====
    key: str
        MMD element to check
    convention: str
        e.g., acdd or acdd_ext
    normalized: dict
        a normalized version of the mmd_elements dict (keys are, e.g.,
        'personnel>organisation>acdd' or
        'personnel>organisation>separator')

    Returns
    =======
    required: int
        if it is required
    repetition: str ('yes' or 'no')
        if repetition is allowed
    comment: str
        a longer string representation for use in the DMH
    separator: str
        sign for separating elements that can be repeated (e.g., ','
        or ';')
    default:
        a default value for elements that are required but missing in
        the netcdf file
    """
    max_occurs_key = key.replace(convention, 'maxOccurs')
    if max_occurs_key in normalized.keys():
        max_occurs = normalized[max_occurs_key]
    else:
        max_occurs = ''
    repetition_allowed = 'yes' if max_occurs not in ['0', '1'] else 'no'
    min_occurs_key = key.replace(convention, 'minOccurs')
    if min_occurs_key in normalized.keys():
        required = int(normalized[min_occurs_key])
    else:
        required = 0
    #separator_key = key.replace(convention, 'separator')
    #if separator_key in normalized.keys():
    #    separator = normalized[separator_key]
    #else:
    #    separator = ''
    #default_key = key.replace(convention, 'default')
    #if default_key in normalized.keys():
    #    default = normalized[default_key]
    #else:
    #    default = ''
    #comment_key = key.replace(convention, 'comment')
    #if comment_key in normalized.keys():
    #    comment = normalized[comment_key]
    #else:
    #    comment = ''
    return required, repetition_allowed#, comment, separator, default

def repetition_allowed(field):
    """ Return True if an MMD/ACDD field has repetition allowed,
    otherwise False.

    Input
    =====
    field : dict
        Dictionary of translations and specifications for an MMD field

    """
    if field is not None and 'maxOccurs' in field.keys():
        rep = True if field['maxOccurs'] not in ['0', '1'] else False
    else:
        rep = True

    return rep

def required(field):
    """ Return True if a field is required, otherwise False.

    Input
    =====
    field : dict
        Dictionary of translations and specifications for an MMD/ACDD
        field.

    """
    if field is not None and 'minOccurs' in field.keys():
        required = bool(int(field['minOccurs']))
    else:
        required = False

    return required

def set_attribute(mmd_field, val, convention, attributes, req='not_required'):
    """ Set the attributes[convention][required] dict from a given
    convention.

    Input
    =====
    mmd_field : str
        The MMD field name that should be translated.
    val : dict
        The value of an MMD translation field as provided in
        `mmd_elements.yaml`.
    convention : str
        'acdd' or 'acdd_ext'. Other conventions may in principle
        also be used.
    attributes : dict
        A dictionary that contains relevant information about the MMD
        to ACDD translation. E.g., the MMD field name, the ACDD
        attribute name, if repetition is allowed, a comment, how to
        separate between repetitions (e.g., by commas), and/or a
        default value.
    req : str, default 'not_required'
        To specify if the attributes[convention]['required'] dict
        should be populated, or if the
        attributes[convention]['not_required'] dict should be
        populated.
    """
    if type(val) is not dict:
        raise ValueError('val input must be dict')
    if convention not in val.keys():
        return None
    for attr in val[convention].keys():
        if req == 'required' and not required(val[convention][attr]):
            continue
        if req == 'not_required' and required(val[convention][attr]):
            continue
        comment, sep, default = '', '', ''
        if val[convention][attr] is not None:
            comment = val[convention][attr].pop('comment', '')
            sep = val[convention][attr].pop('separator', '') 
            default = val[convention][attr].pop('default', '')
        attributes[convention][req].append({
                'mmd_field': mmd_field,
                'attribute': attr,
                'repetition_allowed': repetition_allowed(val[convention][attr]),
                'comment': comment,
                'separator': sep,
                'default': default
            })

def set_attributes(mmd_field, val_dict, attributes):
    """ Loop val_dict to populate attributes dict that contains
    information for the adoc table. Separate between required and not
    required MMD fields.

    Input
    =====
    mmd_field : str
        MMD field name.
    val_dict : dict
        Dictionary with sub-fields of the mmd_field.
    attributes : dict
        Dictionary with information for the adoc table.

    """
    if type(val_dict) is not dict:
        return None
    set_attribute(mmd_field, val_dict, 'acdd', attributes,  req='required')
    set_attribute(mmd_field, val_dict, 'acdd', attributes,  req='not_required')
    set_attribute(mmd_field, val_dict, 'acdd_ext', attributes, req='required')
    set_attribute(mmd_field, val_dict, 'acdd_ext', attributes, req='not_required')
    # Pick sub-dict if any, and repeat
    subdict = val_dict.copy()
    subdict.pop('acdd', '')
    subdict.pop('acdd_ext', '')
    for key, val in subdict.items():
        mmd_field_name = mmd_field + '>' + key
        set_attributes(mmd_field_name, val, attributes)

def nc_attrs_from_yaml():
    """ Create an asciidoc file with text and tables describing the
    translation between ACDD and MMD, plus extra netCDF attributes
    defined as ACDD extensions.
    """
    mmd_yaml = yaml.load(
        resource_string(
            globals()['__name__'].split('.')[0], 'mmd_elements.yaml'
        ), Loader=yaml.FullLoader
    )

    # Flatten dict
    df = pd.json_normalize(mmd_yaml, sep='>')
    normalized = df.to_dict(orient='records')[0]

    attributes = {}
    attributes['message'] = (
        'This file is autogenerated from\n'
        'https://github.com/metno/py-mmd-tools/blob/master/py_mmd_tools/mmd_elements.yaml\n'
        '\n'
        'Please do not update this file manually. The yaml file is used\n'
        'as the authoritative source. If any translations from ACDD to\n'
        'MMD should be changed, the changes should be made in that file.\n'
    )
    attributes['acdd'] = {}
    attributes['acdd']['required'] = []
    attributes['acdd']['not_required'] = []
    attributes['acdd_ext'] = {}
    attributes['acdd_ext']['required'] = []
    attributes['acdd_ext']['not_required'] = []

    for key, val in mmd_yaml.items():
        set_attributes(key, val, attributes)
    
    def is_list(value):
        return isinstance(value, list)

    env = jinja2.Environment(
        loader=jinja2.PackageLoader(globals()['__name__'].split('.')[0], 'templates'),
        autoescape=jinja2.select_autoescape(['html', 'xml']),
        trim_blocks=True, lstrip_blocks=True
    )
    env.filters['is_list'] = is_list
    template = env.get_template('nc_attributes_template.adoc')

    out_doc = template.render(data=attributes)

    return out_doc
