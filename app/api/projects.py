from flask import request, jsonify
from flask_jwt_extended import jwt_required
import uuid

from app.api import api_bp
from app.models import Project
from app import db


@api_bp.route('/projects', methods=['GET'])
def get_projects():
    """Get all projects."""
    projects = Project.query.filter_by(valid=1).order_by(Project.sort.asc()).all()
    return jsonify([project.to_dict() for project in projects])


@api_bp.route('/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Get project by ID."""
    project = Project.query.get(project_id)

    if not project or project.valid != 1:
        return jsonify({'error': 'Project not found'}), 404

    return jsonify(project.to_dict())


@api_bp.route('/projects', methods=['POST'])
@jwt_required()
def create_project():
    """Create a new project."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    project = Project(
        name=data.get('name'),
        code=data.get('code'),
        default_sim_type_id=data.get('defaultSimTypeId'),
        default_solver_id=data.get('defaultSolverId'),
        remark=data.get('remark')
    )

    db.session.add(project)
    db.session.commit()

    return jsonify(project.to_dict()), 201


@api_bp.route('/projects/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    """Update a project."""
    project = Project.query.get(project_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    data = request.get_json()

    if data.get('name'):
        project.name = data['name']
    if data.get('code'):
        project.code = data['code']
    if data.get('defaultSimTypeId') is not None:
        project.default_sim_type_id = data['defaultSimTypeId']
    if data.get('defaultSolverId') is not None:
        project.default_solver_id = data['defaultSolverId']
    if data.get('remark') is not None:
        project.remark = data['remark']

    db.session.commit()

    return jsonify(project.to_dict())


@api_bp.route('/projects/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    """Delete a project (soft delete)."""
    project = Project.query.get(project_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    project.valid = 0
    db.session.commit()

    return jsonify({'message': 'Project deleted successfully'})

