#:after:company/human_resources:paragraph:employee#

En el formulario del empleado podremos ver un resumen de las ausencias que 
tenga asociadas por período, desglosadas en horas.

#:inside:company/human_resources:section:human_resources#

.. inheritref:: employee_leave/employee_leave:section:employee_leave

========================================
Controlar las ausencias de los empleados
========================================

El sistema nos ofrece la opción de configurar y administrar las ausencias de 
los empleados en función  


Dentro del menú de **"Configuración"** podemos indicar la siguiente 
información: 

- "Periodos de ausencias": dónde podemos crear los períodos de ausencia en 
  los que dividiremos el año (o todo un año) como método de control. El 
  sistema lo que nos permite es indicar una fecha de inicio y fin para cada 
  período.
  
- "Tipos de ausencia": podemos crear un listado de diferentes ausencias 
  posibles, lo necesitaremos para clasificar las ausencias de los empleados. 

Dentro del menú de **"Administración"** podemos administrar la siguiente 
información:

.. inheritref:: employee_leave/employee_leave:paragraph:derechos

- "Derechos del empleado": aquí crearemos los derechos generados por 
  trabajador a ausencias. En este caso, la mayoría de veces estas ausencias, 
  derechos como tal, se clasificarán como tipo "Vacaciones" o similar (en 
  función   del nombre que le demos). Dentro del período en que se encuentren 
  dichos días que va a disfrutar el empleado e introducir la "Fecha" en 
  que se meritó este derecho.

  **Ejemplo:** los derechos generados por trabajador a lo largo de un año 
  suelen ser de 23 días, pues en el campo "Horas" (en función de la jornada 
  laboral) deberemos introducir el total de horas a la que estos 23 días 
  pertenecen. En el caso genérico serían 184 horas por empleado.

.. inheritref:: employee_leave/employee_leave:paragraph:pago

- "Pago de ausencias": desde este menú controlaremos el pago y la fecha de 
  concesión de las ausencias de empleado. Podremos rellenar la misma 
  información que en los *Derechos del empleado*, tan solo que ahora será 
  obligatorio añadir una fecha. Esta indicará el día en que se realizo la 
  concesión de esta ausencia.
  
- "Resumen de ausencias": aquí se listarán todos los empleados asociados a la 
  empresa, con cada tipo de ausencia por cada período que hayamos creado. Así 
  como bien dice el nombre del menú tendremos un resumen, que nos mostrará la 
  diferencia entre las horas totales, pagadas, realizadas, programadas, 
  pendientes de aprobar y disponibles.
 
Finalmente fuera de los menús de *Configuración* y *Administración* 
encontraremos el acceso a las **Ausencias**. Aquí es dónde crearemos e 
introduciremos las ausencias solicitadas por los empleados. Nuevamente tendremos 
unas opciones muy similares a las del menú de *Derechos del empleado*, 
deberemos indicar el período y tipo de la ausencia, además de obligatoriamente, 
la fecha de solicitud, las que horas que van suponer y las fechas de inicio y 
fin de la ausencia en cuestión. 

Cómo gestores de ausencias de empleado podremos realizar las siguientes 
acciones:
 
- Cancelar: introducimos una ausencia pero no la identificamos como pendiente, 
  ya que la hemos valorado pero no la refusamos y tampoco la aprobamos. Se 
  podrá volver a pasar al estado *Pendiente* para valorarla de nuevo.
- Refusar: no se acepta una solicitud de ausencia, posteriormente la podemos 
  cancelar y volver a valorar.
- Aprobar: hemos aprobado la solicitud de ausencia
- Realizado: el empleado ha realizado las horas de la ausencia. Aquí se 
  termina y cierra el flujo de la ausencia.