<?xml version="1.0" encoding="utf-8"?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:str="http://exslt.org/strings"
    xmlns:gco="http://www.isotc211.org/2005/gco" 
    xmlns:gmd="http://www.isotc211.org/2005/gmd"
    xmlns:gml="http://www.opengis.net/gml"
    xmlns:mmd="http://www.met.no/schema/mmd"
    xmlns:dif="http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/"
    xmlns:mapping="http://www.met.no/schema/mmd/iso2mmd"      
    version="1.0">
    <xsl:include href="mmd-to-iso.xsl" />
    <xsl:output method="xml" encoding="UTF-8" indent="yes" />
        <xsl:template match="mmd:data_access">
    
        <xsl:element name="gmd:onLine">
            <xsl:element name="gmd:CI_OnlineResource">

                <xsl:element name="gmd:name">
                    <xsl:element name="gco:CharacterString">
                        <xsl:value-of select="mmd:name" />
                    </xsl:element>
                </xsl:element>

                <xsl:element name="gmd:description">
                    <xsl:element name="gco:CharacterString">
                        <xsl:choose>
                           <xsl:when test="mmd:type = 'OGC WMS'">
                              <xsl:value-of select="mmd:type" />
                              <xsl:value-of select="str:replace(mmd:description, ',', ':')" />
                           </xsl:when>
                           <xsl:otherwise>
                              <xsl:value-of select="mmd:type" />
                              <xsl:value-of select="mmd:description" />
                           </xsl:otherwise>
                        </xsl:choose>
                    </xsl:element>
                </xsl:element>

                <xsl:element name="gmd:protocol">
                    <xsl:element name="gco:CharacterString">
                        <!--xsl:value-of select="mmd:type" / -->
                        <xsl:variable name="mmd_da_type" select="normalize-space(./mmd:type)" />
                        <xsl:variable name="mmd_da_mapping" select="document('')/*/mapping:data_access_type[@mmd=$mmd_da_type]/@iso" />
                        <xsl:value-of select="$mmd_da_mapping" />
                    </xsl:element>
                </xsl:element>   

                <xsl:element name="gmd:linkage">
                    <xsl:element name="gmd:URL">
                        <xsl:value-of select="mmd:resource" />
                    </xsl:element>
                </xsl:element>
                
            </xsl:element>
        </xsl:element>
        
    </xsl:template>

    <!-- Mappings for data_access type specification -->
    <mapping:data_access_type iso="OGC:WMS" mmd="OGC WMS" />    
    <mapping:data_access_type iso="OGC:WCS" mmd="OGC WCS" />    
    <mapping:data_access_type iso="OGC:WFS" mmd="OGC WFS" />    
    <mapping:data_access_type iso="WWW:DOWNLOAD-1.0-ftp–download" mmd="FTP" />  
    <mapping:data_access_type iso="WWW:DOWNLOAD-1.0-http–download" mmd="HTTP" />
    <mapping:data_access_type iso="WWW:LINK-1.0-http–opendap" mmd="OPeNDAP" />  
</xsl:stylesheet>

