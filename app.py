from flask import Flask, jsonify, request, render_template
from datetime import datetime

class Nodo:
    def __init__(self, id, nombre, etiqueta, prioridad=None, fecha=None, notas=None, responsables=None):
        self.id = id
        self.nombre = nombre
        self.etiqueta = etiqueta  # esto es para 'proyecto' o 'tarea'
        self.prioridad = prioridad
        self.izquierda = None
        self.derecha = None
        self.fecha = datetime.now() if fecha is None else datetime.strptime(fecha, "%Y-%m-%d")
        self.notas = notas if notas is not None else ""
        self.responsables = responsables if responsables is not None else []

class Arbol_Binario:
    def __init__(self):
        self.raiz = None
        self.contador_id = 0

    def generar_id(self):
        self.contador_id += 1
        return self.contador_id

    def agregar_raiz(self, nombre, etiqueta, prioridad=None, fecha=None, notas=None, responsables=None):
        if self.raiz is None:
            self.raiz = Nodo(self.generar_id(), nombre, etiqueta, prioridad, fecha, notas, responsables)
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
        """
        Busca nodos por nombre, permitiendo búsqueda parcial.
        Args:
            nombre: Texto a buscar
            nodo: Nodo actual (None para comenzar desde la raíz)
        Returns:
            Lista de nodos que coinciden con el criterio de búsqueda
        """
        if nodo is None:
            nodo = self.raiz
            if nodo is None:
                return []

        resultados = []
        nombre = nombre.lower()  # Convertir a minúsculas para búsqueda insensible a mayúsculas

        # Verificar si el nodo actual coincide con el criterio de búsqueda
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
                'puede_agregar_subtareas': self.puede_agregar_hijo(nodo)
            })

        # Buscar en los hijos
        if nodo.izquierda:
            resultados.extend(self.buscar_por_nombre(nombre, nodo.izquierda))
        if nodo.derecha:
            resultados.extend(self.buscar_por_nombre(nombre, nodo.derecha))

        return resultados

    def puede_agregar_hijo(self, nodo):
        return nodo.izquierda is None or nodo.derecha is None

    def agregar_subtarea(self, id_padre, nombre, prioridad, fecha=None, notas=None, responsables=None):
        nodo_padre = self.buscar_nodo(id_padre)
        
        if nodo_padre is None:
            raise Exception("No se encontró la tarea padre")
            
        if not self.puede_agregar_hijo(nodo_padre):
            raise Exception("La tarea ya tiene el máximo de subtareas permitidas (2)")

        nueva_tarea = Nodo(self.generar_id(), nombre, "tarea", prioridad, fecha, notas, responsables)

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

app = Flask(__name__)
arbol = Arbol_Binario()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tareas', methods=['GET'])
def obtener_tareas():
    # Buscar por nombre si se proporciona el parámetro
    nombre = request.args.get('nombre')
    
    if nombre:
        tareas = arbol.buscar_por_nombre(nombre)
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
                datos.get('responsables', [])
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
                datos.get('responsables', [])
            )
            
        return jsonify({
            'mensaje': f'{datos["etiqueta"].capitalize()} agregado correctamente',
            'id_tarea': id_tarea
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