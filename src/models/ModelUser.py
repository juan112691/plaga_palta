from .entities.User import User

class ModelUser():

    @classmethod
    def login(self, db, user):
        try:
            cursor = db.connection.cursor()
            sql = """SELECT id, username, password, fullname, role FROM user 
                    WHERE username = %s"""
            cursor.execute(sql, (user.username,))
            row = cursor.fetchone()
            
            if row:
                if User.check_password(row[2], user.password):
                    return User(row[0], row[1], True, row[3], row[4])
                else:
                    return None
            return None
        except Exception as ex:
            raise Exception(ex)

    @classmethod
    def get_by_id(self, db, id):
        try:
            cursor = db.connection.cursor()
            sql = "SELECT id, username, fullname, role FROM user WHERE id = %s"
            cursor.execute(sql, (id,))
            row = cursor.fetchone()
            
            if row:
                return User(row[0], row[1], None, row[2], row[3])
            return None
        except Exception as ex:
            raise Exception(ex)
    
    @classmethod
    def get_all(self, db):
        try:
            cursor = db.connection.cursor()
            sql = "SELECT id, username, fullname, role FROM user ORDER BY id DESC"
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            usuarios = []
            for row in rows:
                usuarios.append(User(row[0], row[1], None, row[2], row[3]))
            
            return usuarios
        except Exception as ex:
            raise Exception(ex)
    
    @classmethod
    def create(self, db, user, password_plain):
        try:
            cursor = db.connection.cursor()
            
            sql_check = "SELECT id FROM user WHERE username = %s"
            cursor.execute(sql_check, (user.username,))
            
            if cursor.fetchone():
                raise Exception("El usuario ya existe")
            
            hashed_password = User.hash_password(password_plain)
            
            sql = """INSERT INTO user (username, password, fullname, role) 
                     VALUES (%s, %s, %s, %s)"""
            cursor.execute(sql, (user.username, hashed_password, user.fullname, user.role))
            db.connection.commit()
            
            return cursor.lastrowid
        except Exception as ex:
            db.connection.rollback()
            raise Exception(ex)
    
    @classmethod
    def update(self, db, user, password_plain=None):
        try:
            cursor = db.connection.cursor()
            
            if password_plain:
                # Actualizar con nueva contraseña
                hashed_password = User.hash_password(password_plain)
                sql = """UPDATE user 
                         SET username = %s, password = %s, fullname = %s, role = %s 
                         WHERE id = %s"""
                cursor.execute(sql, (user.username, hashed_password, user.fullname, user.role, user.id))
            else:
                # Actualizar sin cambiar contraseña
                sql = """UPDATE user 
                         SET username = %s, fullname = %s, role = %s 
                         WHERE id = %s"""
                cursor.execute(sql, (user.username, user.fullname, user.role, user.id))
            
            db.connection.commit()
            return cursor.rowcount > 0
        except Exception as ex:
            db.connection.rollback()
            raise Exception(ex)
    
    @classmethod
    def delete(self, db, user_id):
        try:
            cursor = db.connection.cursor()
            sql = "DELETE FROM user WHERE id = %s"
            cursor.execute(sql, (user_id,))
            db.connection.commit()
            
            return cursor.rowcount > 0
        except Exception as ex:
            db.connection.rollback()
            raise Exception(ex)
    
    @classmethod
    def username_exists(self, db, username, exclude_id=None):
        try:
            cursor = db.connection.cursor()
            
            if exclude_id:
                sql = "SELECT id FROM user WHERE username = %s AND id != %s"
                cursor.execute(sql, (username, exclude_id))
            else:
                sql = "SELECT id FROM user WHERE username = %s"
                cursor.execute(sql, (username,))
            
            return cursor.fetchone() is not None
        except Exception as ex:
            raise Exception(ex)
    
    @classmethod
    def count_admins(self, db):
        try:
            cursor = db.connection.cursor()
            sql = "SELECT COUNT(*) FROM user WHERE role = 'administrador'"
            cursor.execute(sql)
            row = cursor.fetchone()
            return row[0] if row else 0
        except Exception as ex:
            raise Exception(ex)
