let inputFiles = document.querySelector('#filesInput');
let noOfFiles = document.querySelector('#file-name');

inputFiles.addEventListener('change', function(event){
	let uploadFiles = event.target.files.length;
	noOfFiles.innerHTML = uploadFiles + ' ';
});

// let tableJSON = {{ data | safe }};
let oTable;

document.querySelector("#render").addEventListener('click', renderTable);
document.querySelector("#zoomRange").addEventListener('change', renderTable);
document.querySelector("#thresholdRange").addEventListener('change', renderTable);
document.querySelector("#redRange").addEventListener('change', renderTable);
document.querySelector("#greenRange").addEventListener('change', renderTable);
document.querySelector("#blueRange").addEventListener('change', renderTable);


let lTable = document.getElementById("imgTable");
$('#imgTable thead tr').clone(true).appendTo( '#imgTable thead' ).addClass("clonedTableHead");
lTable.style.display = "none";


function renderTable(event){

	lTable.style.display = "table";
	$('#imgTable thead tr:eq(1) th').each( function (i) {
	var title = $(this).text();
	$(this).html( '<input type="text" placeholder="All" />' );

	$( 'input', this ).on( 'keyup change', function () {

		if ( oTable.column(i).search() !== this.value ) {
			oTable
				.column(i)
				.search( this.value )
				.draw();
			}
		});
	});

	event.preventDefault();
	let zoom = ((document.querySelector("#zoomRange")||{}).value)||"25";
	let threshold = ((document.querySelector("#thresholdRange")||{}).value)||"150";
	let r = ((document.querySelector("#redRange")||{}).value)||"200";
	let g = ((document.querySelector("#greenRange")||{}).value)||"200";
	let b = ((document.querySelector("#blueRange")||{}).value)||"200";
	let rowID = 1;

	oTable = $('#imgTable').DataTable(
		{
			rowCallback: function(row, data, index){
				if(data[8] === 'FALSE'){
					$(row).find('td:eq(8)').css({
						'color': 'red',
						'font-weight': 'bold'
					});
				}

				if(data[3] === 'png'){
					$(row).find('td:eq(3)').css({
						'color': 'steelblue',
						'font-weight': 'bold'
					});
				}

				if(Math.ceil(data[5]/1024) > threshold){
					$(row).find('td:eq(5)').css({
						'color': 'red',
						'font-weight': 'bold'
					});
				}

				$(row).css({
					'background-color': 'rgb(' + r + ',' + g + ',' + b + ')'
				})
			},

			orderCellsTop: true,

			columnDefs: [
				{
					"targets": 1,
					"data": 'TRUE',
					"defaultContent": '<button class="btn info" style="color: steelblue;">TRUE</button>'
				}
			],

			data: tableJSON,
			columns: [
				{
					title: "creative",
					render: function(creative){
						let imgTag = '<img src="' + creative + '"' + ' alt="Img" height="' + zoom + '"></img>';
						let imgURL =  '<a href="/image/creative-img/single-image/' + rowID + '/" target="_blank">' + imgTag + '</a>';
						rowID++;
						return imgURL;
					}
				},
				{ title: "imgBorder" },
				{ title: "imgName" },
				{ title: "imgType" },
				{
					title: "imgSize" ,
					render: function(imgSize){
						let sizeKB = Math.ceil(imgSize/1024) + ' KB';
						return sizeKB;
					}
				},
				{
					title: "imgSizeUnderThreshold" ,
					render: function(imgSizeUnderThreshold){
						let sizeKB = Math.ceil(imgSizeUnderThreshold/1024);
						if (sizeKB <= threshold) { return 'TRUE' } else { return 'FALSE' }
						// return imgSizeUnderThreshold;
					}
				},
				{ title: "imgDimension" },
				{ title: "dimName" },
				{ title: "dimOK" }
			],
			pageLength: 15,
			dom: 'Bfrtip',
			buttons: [
				{
					extend: 'copyHtml5',
					exportOptions: {
						columns: [1, 2, 3, 4, 5, 6, 7, 8]
					}
				},
				{
					extend: 'csvHtml5',
					exportOptions: {
						columns: [1, 2, 3, 4, 5, 6, 7, 8]
					}
				}
			],
			scrollCollapse: true,
			searchable: true,
			paging: true,
			bDestroy: true,
			fixedColumns:   {
				heightMatch: 'none'
			}
		}
	);
};


function colSearch(){

	oTable.columns().every(function (index) {
		$('#imgTable thead tr:eq(1) th:eq(' + index + ') input').on('keyup change', function () {
			table.column($(this).parent().index() + ':visible')
				.search(this.value)
				.draw();
		});
	});
};


$('#imgTable').on( 'click', 'td', function () {
	let trueHTML = '<button class="btn info" style="color: steelblue;">TRUE</button>';
	let falseHTML = '<button class="btn info" style="color: red;">FALSE</button>';
	let html = oTable.cell(this).data();
	let cell = oTable.cell(this);

	if (html === trueHTML) {
		cell.data(falseHTML)

	} else if (html === falseHTML) {
		cell.data(trueHTML)

	} else {

	}

});
