from flask import Blueprint, jsonify, request
from JumpScale import j
import os.path

blueprint_api = Blueprint('blueprint_api', __name__)

def get_blueprint_dict(blueprint):
    return({
        'content': blueprint.content,
        'models': blueprint.models,
        'path': blueprint.path
    })

@blueprint_api.route('/blueprint', methods=['GET'])
def blueprint_get():
    '''
    list all blueprint
    It is handler for GET /blueprint
    '''
    path = request.args.get('path')
    atyourservice=j.atyourservice.get(path)
    return jsonify(blueprints=list(map(get_blueprint_dict, atyourservice.blueprints)))


@blueprint_api.route('/blueprint', methods=['POST'])
def blueprint_post():
    '''
    create a new blueprint
    It is handler for POST /blueprint
    '''
    path = request.args.get('path')
    atyourservice=j.atyourservice.get(path)
    num = max(int (i.path.split('/')[-1].split('_')[0]) for i in atyourservice.blueprints)+1
    j.sal.fs.createEmptyFile(os.path.join(path, 'blueprints', "%d_%s.yaml"%(num,request.json['name'])))
    return jsonify(status=0)


@blueprint_api.route('/blueprint/<name>', methods=['GET'])
def blueprint_byName_get(name):
    '''
    get a blueprint
    It is handler for GET /blueprint/<name>
    '''
    path = request.args.get('path')
    atyourservice=j.atyourservice.get(path)
    blueprint = (i for i in atyourservice.blueprints if i.path.split('/')[-1].split('_')[1].split('.')[0] == name).__next__()
    return jsonify(blueprint=get_blueprint_dict(blueprint))


@blueprint_api.route('/blueprint/<name>', methods=['DELETE'])
def blueprint_byName_delete(name):
    '''
    delete blueprint
    It is handler for DELETE /blueprint/<name>
    '''
    path = request.args.get('path')
    atyourservice=j.atyourservice.get(path)
    dest = os.path.join(path,'_blueprints')
    j.sal.fs.createDir(dest)
    blueprint = (i for i in atyourservice.blueprints if i.path.split('/')[-1].split('_')[1].split('.')[0] == name).__next__()
    j.sal.fs.moveFile(blueprint.path,dest)
    return jsonify(status=0)
