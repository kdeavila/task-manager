from flask import Flask, jsonify, request, render_template
from datetime import datetime

class Nodo:
    def __init__(self, id, nombre, etiqueta, prioridad=None, fecha=None, notas=None, responsables=None, tags=None):
        self.id = id
        self.nombre = nombre
        self.etiqueta = etiqueta
        self.prioridad = prioridad
        self.izquierda = None
        self.derecha = None
        self.fecha = datetime.now() if fecha is None else datetime.strptime(fecha, "%Y-%m-%d")
        self.notas = notas if notas is not None else ""
        self.responsables = responsables if responsables is not None else []
        self.tags = tags if tags is not None else []

class Arbol_Binario:
    def __init__(self):
        self.raiz = None
        self.contador_id = 0

    def generar_id(self):
        self.contador_id += 1
        return self.contador_id

    def agregar_raiz(self, nombre, etiqueta, prioridad=None, fecha=None, notas=None, responsables=None, tags=None):
        if self.raiz is None:
            self.raiz = Nodo(self.generar_id(), nombre, etiqueta, prioridad, fecha, notas, responsables, tags)
            return self.raiz.id
        else:
            raise Exception("Ya existe un proyecto. No se pueden crear más.")

    def buscar_nodo(self, id_nodo, nodo_actual=None):
        if nodo_actual is None:
            nodo_actual = self.raiz
            if nodo_actual is None:
                return None

        if nodo_actual.id == id_nodo:
            return nodo_actual

        if nodo_actual.izquierda:
            resultado = self.buscar_nodo(id_nodo, nodo_actual.izquierda)
            if resultado:
                return resultado

        if nodo_actual.derecha:
            resultado = self.buscar_nodo(id_nodo, nodo_actual.derecha)
            if resultado:
                return resultado

        return None

    def buscar_por_nombre(self, nombre, nodo=None):
        if nodo is None:
            nodo = self.raiz
            if nodo is None:
                return []

        resultados = []
        nombre = nombre.lower()

        nombre_nodo = nodo.nombre.lower()
        if nombre in nombre_nodo:
            resultados.append({
                'id': nodo.id,
                'nombre': nodo.nombre,
                'etiqueta': nodo.etiqueta,
                'prioridad': nodo.prioridad,
                'fecha': nodo.fecha.strftime('%Y-%m-%d'),
                'notas': nodo.notas,
                'responsables': nodo.responsables,
                'tags': nodo.tags,
                'puede_agregar_subtareas': self.puede_agregar_hijo(nodo)
            })

        if nodo.izquierda:
            resultados.extend(self.buscar_por_nombre(nombre, nodo.izquierda))
        if nodo.derecha:
            resultados.extend(self.buscar_por_nombre(nombre, nodo.derecha))

        return resultados

    def buscar_por_tag(self, tag, nodo=None):
        if nodo is None:
            nodo = self.raiz
            if nodo is None:
                return []

        resultados = []
        tag = tag.lower()

        if any(t.lower() == tag for t in nodo.tags):
            resultados.append({
                'id': nodo.id,
                'nombre': nodo.nombre,
                'etiqueta': nodo.etiqueta,
                'prioridad': nodo.prioridad,
                'fecha': nodo.fecha.strftime('%Y-%m-%d'),
                'notas': nodo.notas,
                'responsables': nodo.responsables,
                'tags': nodo.tags,
                'puede_agregar_subtareas': self.puede_agregar_hijo(nodo)
            })

        if nodo.izquierda:
            resultados.extend(self.buscar_por_tag(tag, nodo.izquierda))
        if nodo.derecha:
            resultados.extend(self.buscar_por_tag(tag, nodo.derecha))

        return resultados

    def puede_agregar_hijo(self, nodo):
        return nodo.izquierda is None or nodo.derecha is None

    def agregar_subtarea(self, id_padre, nombre, prioridad, fecha=None, notas=None, responsables=None, tags=None):
        nodo_padre = self.buscar_nodo(id_padre)
        
        if nodo_padre is None:
            raise Exception("No se encontró la tarea padre")
            
        if not self.puede_agregar_hijo(nodo_padre):
            raise Exception("La tarea ya tiene el máximo de subtareas permitidas (2)")

        nueva_tarea = Nodo(self.generar_id(), nombre, "tarea", prioridad, fecha, notas, responsables, tags)

        if prioridad == 'alta':
            if nodo_padre.izquierda is None:
                nodo_padre.izquierda = nueva_tarea
            else:
                nodo_padre.derecha = nueva_tarea
        else:  # prioridad baja
            if nodo_padre.derecha is None:
                nodo_padre.derecha = nueva_tarea
            else:
                nodo_padre.izquierda = nueva_tarea

        return nueva_tarea.id

    def obtener_tareas(self, nodo):
        if nodo is None:
            return []
            
        tareas = [{
            'id': nodo.id,
            'nombre': nodo.nombre,
            'etiqueta': nodo.etiqueta,
            'prioridad': nodo.prioridad,
            'fecha': nodo.fecha.strftime('%Y-%m-%d'),
            'notas': nodo.notas,
            'responsables': nodo.responsables,
            'tags': nodo.tags,
            'puede_agregar_subtareas': self.puede_agregar_hijo(nodo)
        }]
        
        tareas += self.obtener_tareas(nodo.izquierda)
        tareas += self.obtener_tareas(nodo.derecha)
        return tareas
    
    def eliminar_tarea(self, id_tarea):
        if self.raiz is None:
            raise Exception("No hay tareas para eliminar")
            
        if self.raiz.id == id_tarea:
            self.raiz = None
            return True
            
        return self._eliminar_tarea_recursivo(id_tarea, self.raiz)
    
    def _eliminar_tarea_recursivo(self, id_tarea, nodo_actual):
        if nodo_actual is None:
            return False
            
        if nodo_actual.izquierda and nodo_actual.izquierda.id == id_tarea:
            nodo_actual.izquierda = None
            return True
            
        if nodo_actual.derecha and nodo_actual.derecha.id == id_tarea:
            nodo_actual.derecha = None
            return True
            
        return (self._eliminar_tarea_recursivo(id_tarea, nodo_actual.izquierda) or 
                self._eliminar_tarea_recursivo(id_tarea, nodo_actual.derecha))

    def agregar_tags(self, id_tarea, nuevos_tags):
        nodo = self.buscar_nodo(id_tarea)
        if nodo is None:
            raise Exception("Tarea no encontrada")
        
        nuevos_tags = list(set(tag.lower() for tag in nuevos_tags))
        nodo.tags.extend([tag for tag in nuevos_tags if tag not in [t.lower() for t in nodo.tags]])
        return nodo.tags

    def eliminar_tag(self, id_tarea, tag):
        nodo = self.buscar_nodo(id_tarea)
        if nodo is None:
            raise Exception("Tarea no encontrada")
        
        tag = tag.lower()
        nodo.tags = [t for t in nodo.tags if t.lower() != tag]
        return nodo.tags

app = Flask(__name__)
arbol = Arbol_Binario()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tareas', methods=['GET'])
def obtener_tareas():
    nombre = request.args.get('nombre')
    tag = request.args.get('tag')
    
    if nombre:
        tareas = arbol.buscar_por_nombre(nombre)
    elif tag:
        tareas = arbol.buscar_por_tag(tag)
    else:
        tareas = arbol.obtener_tareas(arbol.raiz)
    
    return jsonify({
        'tareas': tareas,
        'proyecto_existe': arbol.raiz is not None
    })

@app.route('/tareas', methods=['POST'])
def agregar_tarea():
    datos = request.json
    if not datos.get('nombre') or not datos.get('etiqueta') or not datos.get('prioridad'):
        return jsonify({'error': 'Faltan datos necesarios'}), 400

    try:
        if datos['etiqueta'] == 'proyecto':
            id_tarea = arbol.agregar_raiz(
                datos['nombre'],
                datos['etiqueta'],
                datos['prioridad'],
                datos.get('fecha'),
                datos.get('notas'),
                datos.get('responsables', []),
                datos.get('tags', [])
            )
        else:
            if not datos.get('id_padre'):
                return jsonify({'error': 'Se requiere id_padre para agregar una subtarea'}), 400
                
            id_tarea = arbol.agregar_subtarea(
                datos['id_padre'],
                datos['nombre'],
                datos['prioridad'],
                datos.get('fecha'),
                datos.get('notas'),
                datos.get('responsables', []),
                datos.get('tags', [])
            )
            
        return jsonify({
            'mensaje': f'{datos["etiqueta"].capitalize()} agregado correctamente',
            'id_tarea': id_tarea
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/tareas/<int:id_tarea>/tags', methods=['POST'])
def agregar_tags(id_tarea):
    datos = request.json
    if not datos.get('tags'):
        return jsonify({'error': 'No se proporcionaron tags'}), 400

    try:
        tags_actualizados = arbol.agregar_tags(id_tarea, datos['tags'])
        return jsonify({
            'mensaje': 'Tags agregados correctamente',
            'tags': tags_actualizados
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/tareas/<int:id_tarea>/tags/<string:tag>', methods=['DELETE'])
def eliminar_tag(id_tarea, tag):
    try:
        tags_actualizados = arbol.eliminar_tag(id_tarea, tag)
        return jsonify({
            'mensaje': 'Tag eliminado correctamente',
            'tags': tags_actualizados
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/tareas/<int:id_tarea>', methods=['DELETE'])
def eliminar_tarea(id_tarea):
    try:
        if arbol.eliminar_tarea(id_tarea):
            return jsonify({'mensaje': 'Tarea eliminada correctamente'})
        return jsonify({'error': 'Tarea no encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)