# NXless Phase 0 sysmodule build.
# Requires an exact Atmosphere 1.11.2 / 5388824 source checkout.

THIS_MAKEFILE := $(abspath $(lastword $(MAKEFILE_LIST)))
SYSMODULE_DIR := $(patsubst %/,%,$(dir $(THIS_MAKEFILE)))
REPO_ROOT := $(abspath $(SYSMODULE_DIR)/..)
NXLESS_ATMOSPHERE_ROOT ?= $(REPO_ROOT)/third_party/Atmosphere
ATMOSPHERE_LIBRARIES_DIR := $(NXLESS_ATMOSPHERE_ROOT)/libraries
STRATOSPHERE_MK := $(ATMOSPHERE_LIBRARIES_DIR)/config/templates/stratosphere.mk

ifeq ($(wildcard $(STRATOSPHERE_MK)),)
$(error Missing $(STRATOSPHERE_MK). Set NXLESS_ATMOSPHERE_ROOT to Atmosphere commit 5388824)
endif

include $(STRATOSPHERE_MK)

TARGET      := nxless-sys
BUILD       := build
SOURCES     := source source/boot source/bsd source/bsd/hos_22_5_0 source/config source/ipc source/platform \
               ../common/src/config ../common/src/diagnostics ../common/src/ipc ../common/src/socket ../common/src/status
DATA        := data
INCLUDES    := include ../common/include
APP_JSON    := $(SYSMODULE_DIR)/config/exefs.nsp.json
TITLE_ID    := 0100000000004E58
OUTPUT_DIR  := $(REPO_ROOT)/output/phase0

ifneq ($(BUILD),$(notdir $(CURDIR)))

export OUTPUT := $(SYSMODULE_DIR)/$(TARGET)
export TOPDIR := $(SYSMODULE_DIR)
export VPATH := $(foreach dir,$(SOURCES),$(SYSMODULE_DIR)/$(dir)) $(foreach dir,$(DATA),$(SYSMODULE_DIR)/$(dir))
export DEPSDIR := $(SYSMODULE_DIR)/$(BUILD)

CPPFILES := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.cpp)))
CFILES   := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.c)))
SFILES   := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.s)))
BINFILES := $(foreach dir,$(DATA),$(notdir $(wildcard $(dir)/*.*)))

ifeq ($(strip $(CPPFILES)),)
export LD := $(CC)
else
export LD := $(CXX)
endif

export OFILES := $(addsuffix .o,$(BINFILES)) $(CPPFILES:.cpp=.o) $(CFILES:.c=.o) $(SFILES:.s=.o)
export INCLUDE := $(foreach dir,$(INCLUDES),-I$(SYSMODULE_DIR)/$(dir)) \
                  $(foreach dir,$(LIBDIRS),-I$(dir)/include) \
                  $(foreach dir,$(AMS_LIBDIRS),-I$(dir)/include) \
                  -I$(CURDIR)/$(BUILD)
export LIBPATHS := $(foreach dir,$(LIBDIRS),-L$(dir)/lib) \
                   $(foreach dir,$(AMS_LIBDIRS),-L$(dir)/$(ATMOSPHERE_LIBRARY_DIR))
export BUILD_EXEFS_SRC := $(TOPDIR)/$(EXEFS_SRC)

.PHONY: all clean dist verify-source

all: verify-source $(BUILD)

verify-source:
	@$(REPO_ROOT)/scripts/verify-atmosphere-source.sh $(NXLESS_ATMOSPHERE_ROOT)
	@$(REPO_ROOT)/scripts/verify-switch-toolchain.sh

$(BUILD):
	@[ -d $@ ] || mkdir -p $@
	@$(MAKE) --no-print-directory -C $(SYSMODULE_DIR)/$(BUILD) -f $(THIS_MAKEFILE) NXLESS_ATMOSPHERE_ROOT=$(NXLESS_ATMOSPHERE_ROOT)

dist: all
	@rm -rf $(OUTPUT_DIR)
	@mkdir -p $(OUTPUT_DIR)/atmosphere/contents/$(TITLE_ID)/flags
	@mkdir -p $(OUTPUT_DIR)/config/nxless
	@cp $(TARGET).nsp $(OUTPUT_DIR)/atmosphere/contents/$(TITLE_ID)/exefs.nsp
	@touch $(OUTPUT_DIR)/atmosphere/contents/$(TITLE_ID)/flags/boot2.flag
	@cp $(REPO_ROOT)/config/nxless/example.toml $(OUTPUT_DIR)/config/nxless/example.toml
	@python3 $(REPO_ROOT)/scripts/verify-phase0-package.py $(OUTPUT_DIR) --repo-root $(REPO_ROOT)
	@cd $(OUTPUT_DIR) && zip -q -r ../../NXless-phase0.zip .
	@echo "Created output/NXless-phase0.zip"

clean:
	@rm -rf $(BUILD) $(TARGET).elf $(TARGET).nso $(TARGET).npdm $(TARGET).nsp $(OUTPUT_DIR) $(REPO_ROOT)/output/NXless-phase0.zip

else

.PHONY: all
DEPENDS := $(OFILES:.o=.d)
all: $(OUTPUT).nsp
$(OUTPUT).nsp: $(OUTPUT).nso $(OUTPUT).npdm
$(OUTPUT).nso: $(OUTPUT).elf
$(OUTPUT).elf: $(OFILES)
$(OFILES): $(ATMOSPHERE_LIBRARIES_DIR)/libstratosphere/$(ATMOSPHERE_LIBRARY_DIR)/libstratosphere.a

%.npdm: $(APP_JSON)
	@npdmtool $< $@

%.bin.o: %.bin
	@$(bin2o)

-include $(DEPENDS)
endif
