# CORRECCIONES REALIZADAS A LA BASE DE CONOCIMIENTO

## Fecha de Corrección: 31 de octubre de 2025, 9:00 AM -03

---

## PROBLEMA IDENTIFICADO

El primer documento de base de conocimiento contenía información INCORRECTA sobre el procedimiento de divorcio en Mendoza conforme la Ley 9120. Específicamente:

### Error Principal:
Se mencionaba que en **divorcio bilateral** existía:
- "Se cita a audiencia inicial"
- "Intento de conciliación"
- "Si hay acuerdo total: se aprueba y dicta sentencia"

**Esto es INCORRECTO según la Ley 9120.**

---

## INFORMACIÓN CORRECTA SEGÚN LEY 9120

### Art. 173 - Divorcio Bilateral

El procedimiento REAL es el siguiente:

#### SUPUESTO 1: ACUERDO TOTAL

```
Presentación (escrito único bilateral con propuesta consensuada)
         ↓
Admisión
         ↓
DECRETO DE DIVORCIO (dentro de 10 días)
         ↓
HOMOLOGACIÓN de la propuesta
         ↓
FIN - NO HAY AUDIENCIA
```

**Puntos críticos:**
- ✓ El juez DICTA DECRETO dentro de 10 días
- ✓ El juez HOMOLOGA (aprueba) la propuesta
- ✗ NO hay audiencia inicial
- ✗ NO hay intento de conciliación
- ✗ El procedimiento es directo: presentación → decreto → homologación

#### SUPUESTO 2: DESACUERDOS PARCIALES

```
Presentación (propuestas diferentes)
         ↓
DECRETO DE DIVORCIO (dentro de 10 días)
         ↓
CITACIÓN A AUDIENCIA (dentro de 10 días)
         ↓
AUDIENCIA (ambos asisten personalmente)
         ↓
Intento de solución consensuada
         ↓
Acuerdo → Homologa | No acuerdo → Jurisdicción abierta
```

**Puntos críticos:**
- ✓ El divorcio ESTÁ DECRETADO (no se discute)
- ✓ La audiencia es solo para resolver EFECTOS
- ✓ Ambos DEBEN asistir PERSONALMENTE
- ✓ Solo ocurre si hay DESACUERDOS PARCIALES

---

## COMPARATIVA: ANTES vs AHORA

### DIVORCIO BILATERAL CON ACUERDO TOTAL

| Aspecto | Error Anterior | Corrección |
|---------|---|---|
| **Audiencia** | Sí, audiencia inicial | NO, sin audiencia |
| **Intento conciliación** | Automático | NO existe |
| **Procedimiento** | Audiencia → Acuerdo → Sentencia | Decreto → Homologación |
| **Plazo** | No especificado | 10 días (decreto) |
| **Resultado** | "Sentencia de divorcio" | "Decreto de divorcio + Homologación" |

### DIVORCIO BILATERAL CON DESACUERDOS

| Aspecto | Información |
|---------|---|
| **Decreto previo** | Sí, dentro de 10 días |
| **Audiencia** | Sí, solo si hay desacuerdos |
| **Asistencia personal** | Obligatoria para ambos |
| **Intento conciliación** | En la audiencia |
| **Resultado sin acuerdo** | Jurisdicción abierta para puntos controvertidos |

---

## ARTÍCULOS RELEVANTES DE LEY 9120 - TEXTO CORRECTO

### Art. 173 - Divorcio Bilateral (Extracto)

"Los cónyuges peticionar el divorcio en escrito único, que contendrá propuesta de regulación de los efectos del divorcio o, en su caso, propuestas unilaterales de cada uno de los cónyuges. Ambas presentaciones requieren patrocinio letrado.

Presentada la petición, el juez **dentro de diez (10) días dictará decreto de divorcio y homologará los acuerdos sobre los efectos del divorcio.**

Si no hay total coincidencia en las propuestas, **el juez dentro de diez (10) días citará a audiencia**, en la que comparecerán ambas partes personalmente con sus respectivos letrados. En la audiencia, se procurará alcanzar solución consensuada sobre los aspectos no coincidentes. Si se llegase a acuerdo, el juez lo homologará en igual acto, sea en forma total o parcial. **El juez podrá rechazar los acuerdos que afecten gravemente los intereses de terceros integrantes del grupo familiar.** Si no se lograre acuerdo, permanecerá abierta la jurisdicción para los aspectos controvertidos..."

### Art. 174 - Divorcio Unilateral (Puntos clave)

- Demandado tiene **5 DÍAS** para responder
- Si no responde: Juez dicta sentencia sin más trámite
- Si propuestas coinciden: Juez homologa
- Si propuestas discordantes: Juez cita a audiencia

### Art. 175 - Omisión de Contestación

"Si el cónyuge demandado no compareciere en el plazo de cinco (5) días...el juez dictará sentencia de divorcio. Si se había invocado separación de hecho previa, la fecha indicada por el peticionario se tendrá por verdadera para los efectos de extinción de la comunidad."

---

## CAMBIOS EN LA BASE DE CONOCIMIENTO

### Documentos Actualizados:

1. **base_conocimiento_divorcio_mendoza_v2.json** [56]
   - Estructura JSON con correcciones
   - Incluye sección "PROCEDIMIENTO_CORRECTO_LEY_9120"
   - Comparativa "antes vs después"

2. **Base_Conocimiento_Divorcio_v2.md** [57]
   - Documento markdown legible
   - Nota prominente de corrección al inicio
   - Diagramas de flujo aclaratorios
   - Procedimientos paso a paso

---

## IMPLICACIONES PRÁCTICAS

### Para un RAG de IA:

1. **Divorcio bilateral con acuerdo total:**
   - Respuesta rápida: "No hay audiencia ni conciliación. Decreto directo dentro de 10 días."
   - Tiempo estimado: 1-2 meses
   - Procedimiento expeditivo

2. **Divorcio bilateral con desacuerdos:**
   - Se DECRETA primero el divorcio
   - Luego se resuelven los efectos en audiencia
   - Tiempo estimado: 2-4 meses

3. **Divorcio unilateral:**
   - Variable según respuesta del demandado
   - Si no responde: Muy rápido (1-2 meses)
   - Si responde distinto: Va a audiencia (2-4 meses)

---

## VALIDACIÓN

**Fuentes consultadas:**
- Ley 9120 - Código Procesal de Familia y Violencia Familiar de Mendoza (oficial de jusmendoza.gob.ar)
- Articulos 173, 174, 175 específicamente

**Período de validez:**
- Información vigente al 31 de octubre de 2025
- Ley 9120 vigente desde 1° de enero de 2019

---

## RECOMENDACIONES PARA USO EN RAG

1. **Priorizar v2.0:** Usar siempre la versión corregida (v2.0)
2. **Distinción clara:** Enfatizar que el divorcio se DECRETA, luego se HOMOLOGAN los efectos
3. **Casos específicos:** Preguntar al usuario si hay acuerdo total o parcial antes de describir el procedimiento
4. **Tiempos realistas:** Advertir que los tiempos pueden variar según complejidad
5. **Asesoramiento:** Recordar que no es asesoramiento legal personalizado

---

*Documento de correcciones - Compilado 31 de octubre de 2025*
