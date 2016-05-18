from flask import Blueprint, jsonify, request
from JumpScale import j

service_api = Blueprint('service_api', __name__)

#@todo (*1*) to christope, queston, is this still required here (kristof), shouldn't this be in separate repo

def get_service_dict(service):
    return({
        'actions':[a for a in dir(service.actions) if not a.startswith('_')],
        'domain':repr(service.domain),
        'parent':repr(service.parent),
        'args':repr(service.args),
        'parents':repr(service.parents),
        'key':repr(service.key),
        'path':repr(service.path),
        'shortkey':repr(service.shortkey),
        'cmd':repr(service.cmd),
        'hrd':repr(service.hrd),
        'hrdhash':repr(service.hrdhash),
        'mongoModel':repr(service.mongoModel),
        'producers':repr(service.producers),
        'version':repr(service.version),
        'name':repr(service.name),
        'recipe':repr(service.recipe),
        'yaml':repr(service.yaml),
        'instance':repr(service.instance),
        'originator':repr(service.originator),
        'role':repr(service.role)
    })


@service_api.route('/service', methods=['GET'])
def service_get():
    '''
    list all services
    It is handler for GET /service
    '''
    path = request.args.get('path')
    atyourservice=j.atyourservice.get(path)
    return jsonify(services=list(map(get_service_dict, atyourservice.services.values())))


@service_api.route('/service/<name>', methods=['GET'])
def service_byName_get(name):
    '''
    get a services
    It is handler for GET /service/<name>
    '''
    path = request.args.get('path')
    atyourservice=j.atyourservice.get(path)
    service = (i for i in atyourservice.services.values() if i.name == name).__next__()
    return jsonify(service=get_service_dict(service))


@service_api.route('/service/<name>/actionlist', methods=['GET'])
def service_byName_actionlist_get(name):
    '''
    get the action list of a services
    It is handler for GET /service/<name>/actionlist
    '''
    path = request.args.get('path')
    atyourservice=j.atyourservice.get(path)
    service = (i for i in atyourservice.services.values() if i.name == name).__next__()
    return jsonify(actionlist=[a for a in dir(service.actions) if not a.startswith('_')])


@service_api.route('/service/<name>/<action>', methods=['POST'])
def service_byName_byAction_post(action, name):
    '''
    perform an action on a services
    It is handler for POST /service/<name>/<action>
    '''
    path = request.args.get('path')
    atyourservice=j.atyourservice.get(path)
    service = (i for i in atyourservice.services.values() if i.name == name).__next__()
    service.runAction(action)
    return jsonify(status=0)
