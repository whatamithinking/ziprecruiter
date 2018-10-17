
from ziprecruiter import ZipRecruiter

z = ZipRecruiter()
z.login( "connormaynes@gmail.com", "scout555" )
z.search( Quantity=20, **{ 'keywords':"automation engineer" } )