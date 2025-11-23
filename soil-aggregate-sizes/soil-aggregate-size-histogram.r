
# Adjust:
setwd("/Users/sam/Google Drive/My Drive/Manuscripts-GD/Coffee-lime-metagenomics-carbon-paper/data-jacob-SOIL-AGREGGATES")
my_data <- read.csv("Juntos-todos.csv", header = TRUE)
#my_data <- read.csv("/Users/sam/Google Drive/My Drive/Manuscripts-GD/Coffee-lime-metagenomics-carbon-paper/data-jacob-SOIL-AGREGGATES/Juntos-todos.csv", header = TRUE)

arachisDF = subset ( my_data, (Arachis == "A")  )
nonArachisDF = subset ( my_data, (Arachis == "NO")  )
arachisAndMicorrizaUnderCoffeeDF = subset ( my_data, (Arachis == "A") & (Micorriza == "M") & (grepl( "CAF", Label, fixed = TRUE) ) )
arachisAndMicorrizaDF = subset ( my_data, (Arachis == "A") & (Micorriza == "M") )
arachisAndNonMicorrizaDF = subset ( my_data, (Arachis == "A") & (Micorriza == "NO") )
nonArachisAndMicorrizaDF = subset ( my_data, (Arachis == "NO") & (Micorriza == "M") )
nonArachisAndNonMicorrizaDF = subset ( my_data, (Arachis == "NO") & (Micorriza == "NO") )

fit_power_law(arachisDF$Area,xmin=20)

#arachisHist = hist(arachisDF$Area,xlim=c(0, 1000), breaks = seq(from=0, to=5000, by=10) )
#nonArachisHist = hist(nonArachisDF$Area,xlim=c(0, 1000), breaks = seq(from=0, to=5000, by=10) )

numBins = 40
#arachisNonArachisHist  = data.frame(arachisHist$breaks[0:numBins], arachisHist$counts[0:numBins], nonArachisHist$counts[0:numBins])

arachisNorm = colSums(arachisNonArachisHist)[2]
nonArachisNorm = colSums(arachisNonArachisHist)[3]



nonArachisAndOtherMicorrizaDF = subset ( my_data, (Arachis == "NO") & ((Micorriza != "NO") & (Micorriza != "NO") ) )
#sanity check
print("length(arachisAndMicorrizaDF) =")
arachisAndMicorrizaNorm = nrow(arachisAndMicorrizaDF)
arachisAndMicorrizaUnderCoffeeNorm = nrow(arachisAndMicorrizaUnderCoffeeDF)
print("length(arachisAndNonMicorrizaDF) =")
arachisAndNonMicorrizaNorm = nrow(arachisAndNonMicorrizaDF)
print("length(nonArachisAndMicorrizaDF) =")
nonArachisAndMicorrizaNorm = nrow(nonArachisAndMicorrizaDF)
print("length(nonArachisAndNonMicorrizaDF) =")
nonArachisAndNonMicorrizaNorm = nrow(nonArachisAndNonMicorrizaDF)


nonArachisAndMicorrizaHist = hist(nonArachisAndMicorrizaDF$Area,xlim=c(0, 1000), breaks = seq(from=0, to=5000, by=10) )
nonArachisAndNonMicorrizaHist = hist(nonArachisAndNonMicorrizaDF$Area,xlim=c(0, 1000), breaks = seq(from=0, to=5000, by=10) )
nonArachisAndMicorrizaAndNonMicorrizaHist  = data.frame(nonArachisAndMicorrizaHist$breaks[0:numBins], nonArachisAndMicorrizaHist$counts[0:numBins], nonArachisAndNonMicorrizaHist$counts[0:numBins])

arachisAndMicorrizaDF = subset ( my_data, (Arachis == "A") & (Micorriza == "M") )
arachisAndNonMicorrizaDF = subset ( my_data, (Arachis == "A") & (Micorriza == "NO") )
arachisAndMicorrizaHist = hist(arachisAndMicorrizaDF$Area,xlim=c(0, 1000), breaks = seq(from=0, to=5000, by=10) )
#temporarily try:
#arachisAndMicorrizaHist = hist(arachisAndMicorrizaUnderCoffeeDF$Area,xlim=c(0, 1000), breaks = seq(from=0, to=5000, by=10) )

arachisAndNonMicorrizaHist = hist(arachisAndNonMicorrizaDF$Area,xlim=c(0, 1000), breaks = seq(from=0, to=5000, by=10) )
arachisAndMicorrizaAndNonMicorrizaHist  = data.frame(arachisAndMicorrizaHist$breaks[0:numBins], arachisAndMicorrizaHist$counts[0:numBins], arachisAndNonMicorrizaHist$counts[0:numBins])

#arachisAndMicorrizaNorm = colSums(arachisAndMicorrizaAndNonMicorrizaHist)[2]
#arachisAndNonMicorrizaNorm = colSums(arachisAndMicorrizaAndNonMicorrizaHist)[3]
#nonArachisAndMicorrizaNorm = colSums(nonArachisAndMicorrizaAndNonMicorrizaHist)[2]
#nonArachisAndNonMicorrizaNorm = colSums(nonArachisAndMicorrizaAndNonMicorrizaHist)[3]


#jpeg(file="histogram-aggregate-size.jpeg")

plot (arachisAndMicorrizaAndNonMicorrizaHist$arachisAndMicorrizaHist.breaks.0.numBins,  arachisAndMicorrizaAndNonMicorrizaHist$arachisAndMicorrizaHist.counts.0.numBins / arachisAndMicorrizaNorm, col="black", cex = 1, type="l", lty = 1 , pch = 3, lwd=3, ylim = c(0, .1), ylab="normalized counts", xlab = expression("Soil aggregate area "(mm^2) ) )
# If you prefer log scale:
#plot (arachisAndMicorrizaAndNonMicorrizaHist$arachisAndMicorrizaHist.breaks.0.numBins,  arachisAndMicorrizaAndNonMicorrizaHist$arachisAndMicorrizaHist.counts.0.numBins / arachisAndMicorrizaNorm, col="black", cex = 1, type="l", lty = 1 , pch = 3, lwd=3,  ylab="normalized counts", xlab = expression("Soil aggregate area "(mm^2) ), log= 'y' )

lines (arachisAndMicorrizaAndNonMicorrizaHist$arachisAndMicorrizaHist.breaks.0.numBins,  arachisAndMicorrizaAndNonMicorrizaHist$arachisAndNonMicorrizaHist.counts.0.numBins / arachisAndNonMicorrizaNorm, col="black", cex = 1, type="l", lty = 2 , pch = 4,  lwd=3)

lines (nonArachisAndMicorrizaAndNonMicorrizaHist$nonArachisAndMicorrizaHist.breaks.0.numBins,  nonArachisAndMicorrizaAndNonMicorrizaHist$nonArachisAndMicorrizaHist.counts.0.numBins / nonArachisAndMicorrizaNorm, col="black", cex = 1, type="l", lty = 1 , pch = 3)
lines (nonArachisAndMicorrizaAndNonMicorrizaHist$nonArachisAndMicorrizaHist.breaks.0.numBins,  nonArachisAndMicorrizaAndNonMicorrizaHist$nonArachisAndNonMicorrizaHist.counts.0.numBins / nonArachisAndNonMicorrizaNorm, col="black", cex = 1, type="l", lty = 2 , pch = 4)

#power law:
#eq = function(x){(x+0)^-1.6}
#lines (nonArachisAndMicorrizaAndNonMicorrizaHist$nonArachisAndMicorrizaHist.breaks.0.numBins, eq(nonArachisAndMicorrizaAndNonMicorrizaHist$nonArachisAndMicorrizaHist.breaks.0.numBins), col="black", cex = 1, type="l", lty = 2 , pch = 4)

legend(100, .1, legend=c(paste("+COVER, +INOC, n=",arachisAndMicorrizaNorm), paste("+COVER, -INOC, n=",arachisAndNonMicorrizaNorm), paste("-COVER, +INOC, n=", nonArachisAndMicorrizaNorm), paste("-COVER, -INOC, n=",nonArachisAndNonMicorrizaNorm)),col=c("black", "black", "black", "black"), lty=c(1,2,1,2), lwd=c(3,3,1,1))





