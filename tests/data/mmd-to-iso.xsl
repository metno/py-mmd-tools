<?xml version="1.0" encoding="utf-8"?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:gco="http://www.isotc211.org/2005/gco" 
    xmlns:gmd="http://www.isotc211.org/2005/gmd"
    xmlns:gml="http://www.opengis.net/gml"
    xmlns:mmd="http://www.met.no/schema/mmd"
    xmlns:dif="http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/"
    xmlns:mapping="http://www.met.no/schema/mmd/iso2mmd"      
    version="1.0">
    <xsl:output method="xml" encoding="UTF-8" indent="yes" />

    <xsl:template match="/mmd:mmd">
        <xsl:element name="gmd:MD_Metadata">

            <gmd:language>
                <gmd:LanguageCode codeList="http://www.loc.gov/standards/iso639-2" codeListValue="eng">English</gmd:LanguageCode>
            </gmd:language>        
            <gmd:characterSet>
                <gmd:MD_CharacterSetCode codeList="http://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_19139_Schemas/resources/Codelist/gmxCodelists.xml#MD_CharacterSetCode"
                               codeListValue="utf8">utf8</gmd:MD_CharacterSetCode>
            </gmd:characterSet>
            
            <gmd:locale>
                <gmd:PT_Locale id="locale-nob">
                    <gmd:languageCode>
                        <gmd:LanguageCode codeList="http://www.loc.gov/standards/iso639-2" codeListValue="nob">Norwegian</gmd:LanguageCode>
                    </gmd:languageCode>
                    <gmd:characterEncoding>
                        <gmd:MD_CharacterSetCode
                            codeList="resources/Codelist/gmxcodelists.xml#MD_CharacterSetCode"
                            codeListValue="utf8"/>
                    </gmd:characterEncoding>
                </gmd:PT_Locale>
            </gmd:locale>            
            
            <gmd:hierarchyLevel>
                <gmd:MD_ScopeCode codeList="http://www.isotc211.org/2005/resources/codeList.xml#MD_ScopeCode"
                                codeListValue="dataset"/>
            </gmd:hierarchyLevel>        

            <xsl:apply-templates select="mmd:metadata_identifier" />
            <xsl:apply-templates select="mmd:dataset_production_status" />
            <xsl:apply-templates select="mmd:last_metadata_update" />
        
            <xsl:element name="gmd:contact">
                <xsl:apply-templates select="mmd:personnel[mmd:role = 'Metadata author']" />
            </xsl:element>
       
        
            <xsl:element name="gmd:identificationInfo">
                <xsl:element name="gmd:MD_DataIdentification">
                
                
                    <xsl:element name="gmd:citation">
                        <xsl:element name="gmd:CI_Citation">
                
                            <!-- non-english elements taken care of within template -->
                            <xsl:apply-templates select="mmd:title[@xml:lang = 'en']" />
                            
                            
                            <xsl:element name="gmd:date">
                                <xsl:element name="gmd:CI_Date">
                                    <xsl:element name="gmd:date">
                                        <xsl:element name="gco:DateTime">
                                            <xsl:value-of select="mmd:dataset_citation/mmd:dataset_release_date" />
                                        </xsl:element>
                                    </xsl:element>
                                    <xsl:element name="gmd:dateType">
                                        <xsl:element name="gmd:CI_DateTypeCode">
                                            <xsl:attribute name="codeList">http://www.isotc211.org/2005/resources/codeList.xml#CI_DateTypeCode</xsl:attribute>
                                            <xsl:attribute name="codeListValue">publication</xsl:attribute>
                                        </xsl:element>
                                    </xsl:element>
                                </xsl:element>
                            </xsl:element>
                            
                            <xsl:element name="gmd:edition">
                                <xsl:element name="gco:CharacterString">
                                    <xsl:value-of select="mmd:dataset_citation/mmd:dataset_release_date" />
                                </xsl:element>
                            </xsl:element>
                            
                            <xsl:element name="gmd:otherCitationDetails">
                                <xsl:element name="gco:CharacterString">
                                    <xsl:value-of select="mmd:dataset_citation/mmd:other_citation_details" />
                                </xsl:element>                            
                            </xsl:element>
                            
                        </xsl:element>
                    </xsl:element>
                    
                    <!-- non-english elements taken care of within template -->
                    <xsl:apply-templates select="mmd:abstract[@xml:lang = 'en']" />
                    
                    <xsl:apply-templates select="mmd:iso_topic_category" />
                    
                    <xsl:element name="gmd:pointOfContact">
                        <xsl:apply-templates select="mmd:personnel[mmd:role != 'Metadata author']" />
                    </xsl:element>
                    
                    <xsl:element name="gmd:extent">
                        <xsl:element name="gmd:EX_Extent">
                            <xsl:apply-templates select="mmd:geographic_extent/mmd:rectangle" />
                            <xsl:apply-templates select="mmd:geographic_extent/mmd:polygon" />
                            <xsl:apply-templates select="mmd:temporal_extent" />
                        </xsl:element>                    
                    </xsl:element>
                    
                    <xsl:element name="gmd:language">
                        <xsl:element name="gmd:LanguageCode">
                            <xsl:attribute name="codeList">http://www.loc.gov/standards/iso639-2</xsl:attribute>
                            <xsl:attribute name="codeListValue">eng</xsl:attribute>
                        </xsl:element>
                    </xsl:element>

                </xsl:element>
            </xsl:element>        
            
            <xsl:element name="gmd:distributionInfo">
                <xsl:element name="gmd:MD_Distribution">
                    <xsl:element name="gmd:transferOptions">
                        <xsl:element name="gmd:MD_DigitalTransferOptions">
                            <xsl:apply-templates select="mmd:data_access" />
                        </xsl:element>
                    </xsl:element>
                </xsl:element>
            </xsl:element>
                
 
            <xsl:element name="gmd:metadataConstraints">
                <xsl:element name="gmd:MD_LegalConstraints">
                    <xsl:element name="gmd:accessConstraints">
                        <xsl:element name="gmd:MD_RestrictionCode">
                            <xsl:attribute name="codeList">http://www.isotc211.org/2005/resources/codeList.xml#MD_RestrictionCode</xsl:attribute>
                            <xsl:attribute name="codeListValue">otherRestrictions</xsl:attribute>
                        </xsl:element>
                    </xsl:element>

                    <xsl:element name="gmd:useConstraints">
                        <xsl:element name="gmd:MD_RestrictionCode">
                            <xsl:attribute name="codeList">http://www.isotc211.org/2005/resources/codeList.xml#MD_RestrictionCode</xsl:attribute>
                            <xsl:attribute name="codeListValue">otherRestrictions</xsl:attribute>
                        </xsl:element>
                    </xsl:element>
                    
                    <xsl:element name="gmd:otherConstraints">
                        <xsl:element name="gco:CharacterString">
                            <xsl:value-of select="mmd:access_constraint" />
                        </xsl:element>
                    </xsl:element>
                    <xsl:element name="gmd:otherConstraints">
                        <xsl:element name="gco:CharacterString">
                            <xsl:value-of select="mmd:use_constraint" />
                        </xsl:element>
                    </xsl:element>
                </xsl:element>
            </xsl:element>
            
            <!--            
            
            <xsl:apply-templates select="mmd:keywords" />
            <xsl:apply-templates select="mmd:project" />
            <xsl:apply-templates select="mmd:instrument" />
            <xsl:apply-templates select="mmd:platform" />
            
             -->

            <gmd:metadataStandardName>
                <gco:CharacterString>ISO 19115:2003/19139</gco:CharacterString>
            </gmd:metadataStandardName>
            <gmd:metadataStandardVersion>
                <gco:CharacterString>1.0</gco:CharacterString>
            </gmd:metadataStandardVersion>
            
        </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:metadata_identifier">
        <xsl:element name="gmd:fileIdentifier">
            <xsl:element name="gco:CharacterString">
                <xsl:value-of select="." />
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:title">
        
        <xsl:element name="gmd:title">
            <xsl:attribute name="xsi:type">PT_FreeText_PropertyType</xsl:attribute>
            <xsl:element name="gco:CharacterString">
                <xsl:value-of select="." />
            </xsl:element>
            <xsl:element name="gmd:PT_FreeText">
                <xsl:element name="gmd:textGroup">
                    <xsl:element name="gmd:LocalisedCharacterString">
                        <xsl:attribute name="locale">#locale-nob</xsl:attribute>
                        <xsl:value-of select="../mmd:title[@xml:lang = 'no']" />
                    </xsl:element>
                </xsl:element>
            </xsl:element>
        </xsl:element>    
        
    </xsl:template>

    <xsl:template match="mmd:abstract">
    
        <xsl:element name="gmd:abstract">
            <xsl:attribute name="xsi:type">PT_FreeText_PropertyType</xsl:attribute>
            <xsl:element name="gco:CharacterString">
                <xsl:value-of select="." />
            </xsl:element>
            <xsl:element name="gmd:PT_FreeText">
                <xsl:element name="gmd:textGroup">
                    <xsl:element name="gmd:LocalisedCharacterString">
                        <xsl:attribute name="locale">#locale-nob</xsl:attribute>
                        <xsl:value-of select="../mmd:abstract[@xml:lang = 'no']" />
                    </xsl:element>
                </xsl:element>
            </xsl:element>
        </xsl:element>
          
    </xsl:template>

    <xsl:template match="mmd:last_metadata_update">
        <xsl:element name="gmd:dateStamp">
            <xsl:element name="gco:DateTime">
                <xsl:value-of select="." />
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:keywords">
        <xsl:for-each select="mmd:keyword">

        </xsl:for-each>
    </xsl:template>

    <xsl:template match="mmd:temporal_extent">
    
        <xsl:element name="gmd:temporalElement">
            <xsl:element name="gmd:EX_TemporalExtent">
                <xsl:element name="gmd:extent">
                    <xsl:element name="gml:TimePeriod">
                        <xsl:attribute name="id">
                            <xsl:number />
                        </xsl:attribute>
                        <xsl:element name="gml:beginPosition">
                            <xsl:value-of select="mmd:start_date" />
                        </xsl:element>
                        <xsl:element name="gml:endPosition">
                            <xsl:value-of select="mmd:end_date" />
                        </xsl:element>
                    </xsl:element>
                </xsl:element>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:geographic_extent/mmd:rectangle">
    
        <xsl:element name="gmd:geographicElement">
            <xsl:element name="gmd:EX_GeographicBoundingBox">
                <xsl:element name="gmd:westBoundLongitude">
                     <xsl:element name="gco:Decimal">
                        <xsl:value-of select="mmd:west" />
                    </xsl:element>
                </xsl:element>
                <xsl:element name="gmd:eastBoundLongitude">
                    <xsl:element name="gco:Decimal">
                        <xsl:value-of select="mmd:east" />
                    </xsl:element>
                </xsl:element>
                <xsl:element name="gmd:southBoundLatitude">
                    <xsl:element name="gco:Decimal">
                        <xsl:value-of select="mmd:south" />
                    </xsl:element>
                </xsl:element>
                <xsl:element name="gmd:northBoundLatitude">
                    <xsl:element name="gco:Decimal">
                        <xsl:value-of select="mmd:north" />
                    </xsl:element>
                </xsl:element>
            </xsl:element>
        </xsl:element>                

    </xsl:template>
    
    <xsl:template match="mmd:geographic_extent/mmd:polygon">
    
        <xsl:element name="gmd:geographicElement">
            <xsl:element name="gmd:EX_BoundingPolygon">
                <xsl:element name="gmd:polygon">
                    <xsl:copy-of select="gml:Polygon" />
                </xsl:element>
            </xsl:element>
        </xsl:element>                

    </xsl:template>    

    <xsl:template match="mmd:data_access">
    
        <xsl:element name="gmd:onLine">
            <xsl:element name="gmd:CI_OnlineResource">
                <xsl:element name="gmd:linkage">
                    <xsl:element name="gmd:URL">
                        <xsl:variable name="myprot" select="normalize-space(./mmd:type)" />
                        <xsl:choose>
                            <xsl:when test="contains($myprot,'OGC WMS')">
                                <xsl:variable name="myurl" select="normalize-space(./mmd:resource)" />
                                <xsl:choose>
                                    <xsl:when test="contains($myurl,'?SERVICE=WMS&amp;REQUEST=GetCapabilities')">
                                        <xsl:value-of select="mmd:resource" />
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:value-of select="concat($myurl,'?SERVICE=WMS&amp;REQUEST=GetCapabilities')" />
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="mmd:resource" />
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
                <xsl:element name="gmd:name">
                    <xsl:element name="gco:CharacterString">
                        <xsl:value-of select="mmd:name" />
                    </xsl:element>
                </xsl:element>
                <xsl:element name="gmd:description">
                    <xsl:element name="gco:CharacterString">
                        <xsl:value-of select="mmd:description" />
                    </xsl:element>
                </xsl:element>                
            </xsl:element>
        </xsl:element>
        
    </xsl:template>
    
    
    <xsl:template match="mmd:personnel">
    
        <xsl:element name="gmd:CI_ResponsibleParty">
            <xsl:element name="gmd:individualName">
                <xsl:element name="gco:CharacterString">
                    <xsl:value-of select="mmd:name" />
                </xsl:element>
            </xsl:element>
            
            <xsl:element name="gmd:organisationName">
                <xsl:element name="gco:CharacterString">
                    <xsl:value-of select="mmd:organisation" />
                </xsl:element>
            </xsl:element>            
            
            <xsl:element name="gmd:contactInfo">
                <xsl:element name="gmd:CI_Contact">
                    <xsl:element name="gmd:phone">
                        <xsl:element name="gmd:CI_Telephone">
                            <xsl:element name="gmd:voice">
                                <xsl:element name="gco:CharacterString">
                                    <xsl:value-of select="mmd:phone" />
                                </xsl:element>
                            </xsl:element>
                        </xsl:element>
                    </xsl:element>
                    <xsl:element name="gmd:address">
                        <xsl:element name="gmd:CI_Address">
                            <xsl:element name="gmd:deliveryPoint">
                                <xsl:element name="gco:CharacterString">
                                    <xsl:value-of select="mmd:contact_address/address" />
                                </xsl:element>
                            </xsl:element>
                            <xsl:element name="gmd:city">
                                <xsl:element name="gco:CharacterString">
                                    <xsl:value-of select="mmd:contact_address/city" />
                                </xsl:element>
                            </xsl:element>
                            <xsl:element name="gmd:postalCode">
                                <xsl:element name="gco:CharacterString">
                                    <xsl:value-of select="mmd:contact_address/postal_code" />
                                </xsl:element>
                            </xsl:element>
                            <xsl:element name="gmd:country">
                                <xsl:element name="gco:CharacterString">
                                    <xsl:value-of select="mmd:contact_address/country" />
                                </xsl:element>
                            </xsl:element>
                            <xsl:element name="gmd:electronicMailAddress">
                                <xsl:element name="gco:CharacterString">
                                    <xsl:value-of select="mmd:email" />
                                </xsl:element>
                            </xsl:element>
                        </xsl:element>
                    </xsl:element>
                </xsl:element>
            </xsl:element>
            
            
            <xsl:element name="gmd:role">
                <xsl:element name="gmd:CI_RoleCode">
                    <xsl:attribute name="codeList">http://www.isotc211.org/2005/resources/codeList.xml#CI_RoleCode</xsl:attribute>
                    <xsl:attribute name="codeListValue">
                        <xsl:choose>
                            <xsl:when test="mmd:role = 'Principal investigator'">
                                <xsl:text>principalInvestigator</xsl:text>
                            </xsl:when>
                            <xsl:when test="mmd:role = 'Technical contact'">
                                <xsl:text>pointOfContact</xsl:text>
                            </xsl:when>
                            <xsl:when test="mmd:role = 'Metadata author'">
                                <xsl:text>author</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>pointOfContact</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:attribute>
                </xsl:element>             
            </xsl:element>
        </xsl:element>
    
    </xsl:template>

    <xsl:template match="mmd:project">

    </xsl:template>

    <xsl:template match="mmd:instrument">

    </xsl:template>

    <xsl:template match="mmd:platform">

    </xsl:template>

    <xsl:template match="mmd:dataset_production_status">

        <xsl:element name="gmd:status">
            <xsl:variable name="mmd_status" select="normalize-space(.)" />
            <xsl:variable name="mmd_status_mapping" select="document('')/*/mapping:dataset_status[@mmd=$mmd_status]/@iso" />
            <xsl:value-of select="$mmd_status_mapping" />
        </xsl:element>

    </xsl:template>

    <xsl:template match="mmd:iso_topic_category">
        <xsl:element name="gmd:topicCategory">
            <xsl:element name="gmd:MD_TopicCategoryCode">
                <xsl:value-of select="." />
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- Mappings for dataset_production_status -->
    <mapping:dataset_status iso="completed" mmd="Complete" />
    <mapping:dataset_status iso="obsolete" mmd="Obsolete" />
    <mapping:dataset_status iso="onGoing" mmd="In Work" />
    <mapping:dataset_status iso="planned" mmd="Planned" />    

    <!-- Mappings for data_access type specification -->
    <mapping:data_access_type iso="OGC:WMS" mmd="OGC WMS" />    
    <mapping:data_access_type iso="OGC:WCS" mmd="OGC WCS" />    
    <mapping:data_access_type iso="OGC:WFS" mmd="OGC WFS" />    
    <mapping:data_access_type iso="WWW:DOWNLOAD-1.0-ftp–download" mmd="FTP" />  
    <mapping:data_access_type iso="WWW:DOWNLOAD-1.0-http–download" mmd="HTTP" />
    <mapping:data_access_type iso="WWW:LINK-1.0-http–opendap" mmd="OPeNDAP" />  

</xsl:stylesheet>
