from flask import Flask, jsonify, request
from webapp.user_login_app import token_required
from db.flaskdbreader import FlaskDBReader
from db.flaskdbwriter import FlaskDBWriter

app = Flask(__name__)

reader = FlaskDBReader(app)
writer = FlaskDBWriter(app)


@app.route('/active-images', methods=['GET'])
@token_required
def get_num_images_in_active_threads(current_user):
    if not current_user['admin']:
        return jsonify({'message': 'cannot perform that function'})

    return jsonify({'active-images': reader.get_imageno()})


@app.route('/active-replies', methods=['GET'])
@token_required
def get_num_replies_in_active_threads(current_user):
    if not current_user['admin']:
        return jsonify({'message': 'cannot perform that function'})

    return jsonify({'active-replies': reader.get_replyno()})


@app.route('/posts/from', methods=['GET'])
@token_required
def get_posts_time_span(current_user):
    if not current_user['admin']:
        return jsonify({'message': 'cannot perform that function'})

    start = request.args.get('start')
    end = request.args.get('end')
    return jsonify({'posts': reader.get_posts_timespan(start)})


@app.route('/posts/last', methods=['GET'])
@token_required
def get_Latest_n_posts(current_user, field=None):
    if not current_user['admin']:
        return jsonify({'message': 'cannot perform that function'})

    npst = request.args.get('n')
    return jsonify({'posts': reader.get_latest_n_posts(npst)})


@app.route('/stats/country/from', methods=['GET'])
@token_required
def get_country_stats(current_user):
    if not current_user['admin']:
        return jsonify({'message': 'cannot perform that function'})

    start = request.args.get('start')
    end = request.args.get('end')
    return jsonify({f'cstats': reader.get_flag_stats(int(start), int(end))})


@app.route('/stats/fetch', methods=['GET'])
@token_required
def get_board_stats(current_user):
    if not current_user['admin']:
        return jsonify({'message': 'cannot perform that function'})

    start = request.args.get('start')
    end = request.args.get('end')
    return jsonify({f'bstats': reader.get_boardstats(int(start), int(end))})


@app.route('/threads', methods=['GET'])
@token_required
def get_thread(current_user):
    if not current_user['admin']:
        return jsonify({'message': 'cannot perform that function'})

    thrd_no = request.args.get('thrd_no')
    return jsonify({f'threads': reader.get_thread(thrd_no=int(thrd_no))})


@app.route('/threads', methods=['POST'])
@token_required
def add_thread(current_user):
    if not current_user['admin']:
        return jsonify({'message': 'cannot perform that function'})

    thread = request.get_json(force=True)
    return writer.create_thread(thread)


@app.route('/threads', methods=['DELETE'])
@token_required
def delete_thread(current_user):
    if not current_user['admin']:
        return jsonify({'message': 'cannot perform that function'})

    thrd_no = request.args.get('thrd_no')
    return writer.delete_thread(thrd_no)


@app.route('/threads/posts', methods=['POST'])
@token_required
def add_post_on_thread(current_user):
    if not current_user['admin']:
        return jsonify({'message': 'cannot perform that function'})

    thread = request.get_json(force=True)
    return writer.post_on_thread(thread)


@app.route('/threads/posts', methods=['GET'])
@token_required
def get_posts_from_thread(current_user):
    if not current_user['admin']:
        return jsonify({'message': 'cannot perform that function'})

    thrd_no = request.args.get('thrd_no')
    return jsonify({'posts': reader.get_posts_from_thread(tnum=thrd_no)})


@app.route('/threads/attachment/max', methods=['GET'])
@token_required
def get_max_size(current_user):
    if not current_user['admin']:
        return jsonify({'message': 'cannot perform that function'})

    return jsonify({'biggest-att': reader.get_biggest_attachment()})


@app.route('/threads/attachment', methods=['GET'])
@token_required
def get_att(current_user):
    if not current_user['admin']:
        return jsonify({'message': 'cannot perform that function'})

    return jsonify({'att': reader.get_attachment()})


if __name__ == "__main__":
    app.run(debug=False)
