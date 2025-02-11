from flask import request, jsonify, g
from flask_cors import cross_origin
from datetime import datetime, timezone
import math
import sqlite3

def load(app):
  # todo /study_sessions POST

  @app.route('/api/study-sessions', methods=['GET'])
  @cross_origin()
  def get_study_sessions():
    try:
      cursor = app.db.cursor()
      
      # Get pagination parameters
      page = request.args.get('page', 1, type=int)
      per_page = request.args.get('per_page', 10, type=int)
      offset = (page - 1) * per_page

      # Get total count
      cursor.execute('''
        SELECT COUNT(*) as count 
        FROM study_sessions ss
        JOIN groups g ON g.id = ss.group_id
        JOIN study_activities sa ON sa.id = ss.study_activity_id
      ''')
      total_count = cursor.fetchone()['count']

      # Get paginated sessions
      cursor.execute('''
        SELECT 
          ss.id,
          ss.group_id,
          g.name as group_name,
          sa.id as activity_id,
          sa.name as activity_name,
          ss.created_at,
          COUNT(wri.id) as review_items_count
        FROM study_sessions ss
        JOIN groups g ON g.id = ss.group_id
        JOIN study_activities sa ON sa.id = ss.study_activity_id
        LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
        GROUP BY ss.id
        ORDER BY ss.created_at DESC
        LIMIT ? OFFSET ?
      ''', (per_page, offset))
      sessions = cursor.fetchall()

      return jsonify({
        'items': [{
          'id': session['id'],
          'group_id': session['group_id'],
          'group_name': session['group_name'],
          'activity_id': session['activity_id'],
          'activity_name': session['activity_name'],
          'start_time': session['created_at'],
          'end_time': session['created_at'],  # For now, just use the same time since we don't track end time
          'review_items_count': session['review_items_count']
        } for session in sessions],
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': math.ceil(total_count / per_page)
      })
    except Exception as e:
      return jsonify({"error": str(e)}), 500

  @app.route('/api/study-sessions', methods=['POST'])
  @cross_origin()
  def create_study_session():
      if not request.is_json:
          return jsonify({'error': 'Content-Type must be application/json'}), 400
      
      def validate_study_session(data):
          required_fields = ['group_id', 'study_activity_id']
          return all(field in data for field in required_fields)

      data = request.get_json()
      
      if not validate_study_session(data):
          return jsonify({'error': 'Missing required fields. Need group_id and study_activity_id'}), 400

      new_session = {
          'group_id': data['group_id'],
          'study_activity_id': data['study_activity_id'],
          'created_at': datetime.now(timezone.utc).isoformat()
      }

      try:
          cursor = app.db.cursor()
          
          # Log incoming data
          print(f"Received data: {new_session}")
          
          # Verify group_id exists with detailed logging
          cursor.execute('SELECT * FROM groups WHERE id = ?', (new_session['group_id'],))
          group = cursor.fetchone()
          if not group:
              print(f"Group with id {new_session['group_id']} does not exist")
              cursor.execute('SELECT * FROM groups')
              print("Available groups:", [dict(row) for row in cursor.fetchall()])
              return jsonify({'error': f'Group with id {new_session["group_id"]} does not exist'}), 400
          
          # Verify study_activity_id exists with detailed logging
          cursor.execute('SELECT * FROM study_activities WHERE id = ?', (new_session['study_activity_id'],))
          activity = cursor.fetchone()
          if not activity:
              print(f"Study activity with id {new_session['study_activity_id']} does not exist")
              cursor.execute('SELECT * FROM study_activities')
              print("Available study activities:", [dict(row) for row in cursor.fetchall()])
              return jsonify({'error': f'Study activity with id {new_session["study_activity_id"]} does not exist'}), 400
          
          cursor.execute('''
              INSERT INTO study_sessions (group_id, study_activity_id, created_at)
              VALUES (?, ?, ?)
          ''', (new_session['group_id'], new_session['study_activity_id'], 
                new_session['created_at']))
          
          app.db.commit()
          new_session['id'] = cursor.lastrowid
          
          print(f"Study session created successfully: {new_session}")
          
          return jsonify({
              'message': 'Study session created successfully',
              'session': new_session
          }), 201
      except sqlite3.IntegrityError as e:
          # Handle foreign key constraint violations
          print(f"Integrity Error: {e}")
          return jsonify({'error': f'Integrity Error: {str(e)}'}), 400
      except Exception as e:
          import traceback
          print("Unexpected error occurred:")
          traceback.print_exc()  # Print full traceback to console
          return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

  @app.route('/api/study-sessions/<id>', methods=['GET'])
  @cross_origin()
  def get_study_session(id):
    try:
      cursor = app.db.cursor()
      
      # Get session details
      cursor.execute('''
        SELECT 
          ss.id,
          ss.group_id,
          g.name as group_name,
          sa.id as activity_id,
          sa.name as activity_name,
          ss.created_at,
          COUNT(wri.id) as review_items_count
        FROM study_sessions ss
        JOIN groups g ON g.id = ss.group_id
        JOIN study_activities sa ON sa.id = ss.study_activity_id
        LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
        WHERE ss.id = ?
        GROUP BY ss.id
      ''', (id,))
      
      session = cursor.fetchone()
      if not session:
        return jsonify({"error": "Study session not found"}), 404

      # Get pagination parameters
      page = request.args.get('page', 1, type=int)
      per_page = request.args.get('per_page', 10, type=int)
      offset = (page - 1) * per_page

      # Get the words reviewed in this session with their review status
      cursor.execute('''
        SELECT 
          w.*,
          COALESCE(SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END), 0) as session_correct_count,
          COALESCE(SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END), 0) as session_wrong_count
        FROM words w
        JOIN word_review_items wri ON wri.word_id = w.id
        WHERE wri.study_session_id = ?
        GROUP BY w.id
        ORDER BY w.kanji
        LIMIT ? OFFSET ?
      ''', (id, per_page, offset))
      
      words = cursor.fetchall()

      # Get total count of words
      cursor.execute('''
        SELECT COUNT(DISTINCT w.id) as count
        FROM words w
        JOIN word_review_items wri ON wri.word_id = w.id
        WHERE wri.study_session_id = ?
      ''', (id,))
      
      total_count = cursor.fetchone()['count']

      return jsonify({
        'session': {
          'id': session['id'],
          'group_id': session['group_id'],
          'group_name': session['group_name'],
          'activity_id': session['activity_id'],
          'activity_name': session['activity_name'],
          'start_time': session['created_at'],
          'end_time': session['created_at'],  # For now, just use the same time
          'review_items_count': session['review_items_count']
        },
        'words': [{
          'id': word['id'],
          'kanji': word['kanji'],
          'romaji': word['romaji'],
          'english': word['english'],
          'correct_count': word['session_correct_count'],
          'wrong_count': word['session_wrong_count']
        } for word in words],
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': math.ceil(total_count / per_page)
      })
    except Exception as e:
      return jsonify({"error": str(e)}), 500

  # todo POST /study_sessions/:id/review

  @app.route('/api/study-sessions/reset', methods=['POST'])
  @cross_origin()
  def reset_study_sessions():
    try:
      cursor = app.db.cursor()
      
      # First delete all word review items since they have foreign key constraints
      cursor.execute('DELETE FROM word_review_items')
      
      # Then delete all study sessions
      cursor.execute('DELETE FROM study_sessions')
      
      app.db.commit()
      
      return jsonify({"message": "Study history cleared successfully"}), 200
    except Exception as e:
      return jsonify({"error": str(e)}), 500